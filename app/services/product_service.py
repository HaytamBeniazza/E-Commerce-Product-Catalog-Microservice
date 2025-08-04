"""ProductModel service for managing ProductModel operations.

This module provides functionality for ProductModel CRUD operations,
search, filtering, inventory management, and analytics.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.brand import Brand
from app.models.category import Category
from app.models.product import Product as ProductModel, ProductImage, ProductStatus, ProductType
from app.schemas.common import PaginationParams, PaginatedResponse
from app.schemas.product import (
    Product,
    ProductCreate,
    ProductUpdate,
    ProductSearch,
    ProductBulkOperation,
    ProductStats
)
from app.services.cache_service import CacheService


class ProductService:
    """Service for managing ProductModel operations."""
    
    def __init__(self, db_session: AsyncSession, cache_service: Optional[CacheService] = None):
        """Initialize ProductModel service.
        
        Args:
            db_session: Database session
            cache_service: Cache service for storing ProductModel data
        """
        self.db = db_session
        self.cache = cache_service
    
    async def create_product(self, product_data: ProductCreate, user_id: str) -> ProductModel:
        """Create a new ProductModel.
        
        Args:
            product_data: ProductModel creation data
            user_id: ID of user creating the product
            
        Returns:
            Created ProductModel object
            
        Raises:
            HTTPException: If SKU already exists or categories/brand not found
        """
        # Check if SKU already exists
        existing_product = await self._get_product_by_sku(product_data.sku)
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ProductModel with SKU '{product_data.sku}' already exists"
            )
        
        # Validate categories exist
        categories = await self._validate_categories(product_data.category_ids)
        
        # Validate brand exists (if provided)
        brand = None
        if product_data.brand_id:
            brand = await self._validate_brand(product_data.brand_id)
        
        # Create product
        ProductModel = ProductModel(
            name=product_data.name,
            description=product_data.description,
            short_description=product_data.short_description,
            sku=product_data.sku,
            barcode=product_data.barcode,
            price=product_data.price,
            compare_price=product_data.compare_price,
            cost_price=product_data.cost_price,
            currency=product_data.currency,
            weight=product_data.weight,
            dimensions=product_data.dimensions,
            stock_quantity=product_data.stock_quantity,
            low_stock_threshold=product_data.low_stock_threshold,
            track_inventory=product_data.track_inventory,
            allow_backorder=product_data.allow_backorder,
            product_type=product_data.product_type,
            status=product_data.status,
            is_featured=product_data.is_featured,
            is_digital=product_data.is_digital,
            requires_shipping=product_data.requires_shipping,
            meta_title=product_data.meta_title,
            meta_description=product_data.meta_description,
            meta_keywords=product_data.meta_keywords,
            tags=product_data.tags,
            attributes=product_data.attributes,
            brand_id=product_data.brand_id,
            created_by=user_id
        )
        
        # Set categories
        ProductModel.categories = categories
        
        self.db.add(ProductModel)
        await self.db.flush()  # Get ProductModel ID
        
        # Create ProductModel images
        if product_data.images:
            for img_data in product_data.images:
                image = ProductImage(
                    product_id=ProductModel.id,
                    url=img_data.url,
                    alt_text=img_data.alt_text,
                    display_order=img_data.display_order,
                    is_primary=img_data.is_primary
                )
                self.db.add(image)
        
        await self.db.commit()
        await self.db.refresh(ProductModel)
        
        # Load relationships
        await self.db.refresh(ProductModel, ['categories', 'brand', 'images'])
        
        # Update category ProductModel counts
        await self._update_category_product_counts(product_data.category_ids, increment=True)
        
        # Update brand ProductModel count
        if product_data.brand_id:
            await self._update_brand_product_count(product_data.brand_id, increment=True)
        
        # Cache product
        if self.cache:
            await self.cache.set_product(ProductModel)
        
        return product
    
    async def get_product(self, product_id: str, increment_view: bool = True) -> Optional[ProductModel]:
        """Get ProductModel by ID.
        
        Args:
            product_id: ProductModel ID
            increment_view: Whether to increment view count
            
        Returns:
            ProductModel object or None if not found
        """
        # Try cache first
        if self.cache:
            cached_product = await self.cache.get_product(product_id)
            if cached_product:
                if increment_view:
                    await self._increment_view_count(product_id)
                return cached_product
        
        # Query database
        result = await self.db.execute(
            select(ProductModel)
            .options(
                selectinload(ProductModel.categories),
                selectinload(ProductModel.brand),
                selectinload(ProductModel.images)
            )
            .where(ProductModel.id == product_id)
        )
        ProductModel = result.scalar_one_or_none()
        
        if ProductModel:
            # Cache product
            if self.cache:
                await self.cache.set_product(ProductModel)
            
            # Increment view count
            if increment_view:
                await self._increment_view_count(product_id)
        
        return product
    
    async def get_product_by_slug(self, slug: str, increment_view: bool = True) -> Optional[ProductModel]:
        """Get ProductModel by slug.
        
        Args:
            slug: ProductModel slug
            increment_view: Whether to increment view count
            
        Returns:
            ProductModel object or None if not found
        """
        result = await self.db.execute(
            select(ProductModel)
            .options(
                selectinload(ProductModel.categories),
                selectinload(ProductModel.brand),
                selectinload(ProductModel.images)
            )
            .where(ProductModel.slug == slug)
        )
        ProductModel = result.scalar_one_or_none()
        
        if ProductModel and increment_view:
            await self._increment_view_count(str(ProductModel.id))
        
        return product
    
    async def update_product(self, product_id: str, product_data: ProductUpdate, user_id: str) -> ProductModel:
        """Update an existing ProductModel.
        
        Args:
            product_id: ProductModel ID
            product_data: ProductModel update data
            user_id: ID of user updating the product
            
        Returns:
            Updated ProductModel object
            
        Raises:
            HTTPException: If ProductModel not found or SKU conflict
        """
        # Get existing product
        ProductModel = await self.get_product(product_id, increment_view=False)
        if not ProductModel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ProductModel not found"
            )
        
        # Check SKU conflict if SKU is being updated
        if product_data.sku and product_data.sku != ProductModel.sku:
            existing_product = await self._get_product_by_sku(product_data.sku)
            if existing_product and existing_product.id != ProductModel.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"ProductModel with SKU '{product_data.sku}' already exists"
                )
        
        # Validate categories if being updated
        old_category_ids = [str(cat.id) for cat in ProductModel.categories]
        new_categories = None
        if product_data.category_ids is not None:
            new_categories = await self._validate_categories(product_data.category_ids)
        
        # Validate brand if being updated
        if product_data.brand_id is not None:
            if product_data.brand_id:
                await self._validate_brand(product_data.brand_id)
        
        # Update ProductModel fields
        update_data = product_data.dict(exclude_unset=True, exclude={'category_ids'})
        update_data['updated_by'] = user_id
        
        for field, value in update_data.items():
            setattr(ProductModel, field, value)
        
        # Update categories if provided
        if new_categories is not None:
            ProductModel.categories = new_categories
        
        await self.db.commit()
        await self.db.refresh(ProductModel, ['categories', 'brand', 'images'])
        
        # Update category ProductModel counts
        if product_data.category_ids is not None:
            new_category_ids = product_data.category_ids
            
            # Decrement old categories
            removed_categories = set(old_category_ids) - set(new_category_ids)
            if removed_categories:
                await self._update_category_product_counts(list(removed_categories), increment=False)
            
            # Increment new categories
            added_categories = set(new_category_ids) - set(old_category_ids)
            if added_categories:
                await self._update_category_product_counts(list(added_categories), increment=True)
        
        # Update brand ProductModel count
        if product_data.brand_id is not None:
            old_brand_id = str(ProductModel.brand_id) if ProductModel.brand_id else None
            new_brand_id = product_data.brand_id
            
            if old_brand_id != new_brand_id:
                if old_brand_id:
                    await self._update_brand_product_count(old_brand_id, increment=False)
                if new_brand_id:
                    await self._update_brand_product_count(new_brand_id, increment=True)
        
        # Clear cache
        if self.cache:
            await self.cache.delete_product(product_id)
        
        return product
    
    async def delete_product(self, product_id: str) -> None:
        """Delete a ProductModel.
        
        Args:
            product_id: ProductModel ID
            
        Raises:
            HTTPException: If ProductModel not found
        """
        ProductModel = await self.get_product(product_id, increment_view=False)
        if not ProductModel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ProductModel not found"
            )
        
        # Get category and brand IDs for count updates
        category_ids = [str(cat.id) for cat in ProductModel.categories]
        brand_id = str(ProductModel.brand_id) if ProductModel.brand_id else None
        
        # Delete ProductModel (cascade will handle images)
        await self.db.delete(ProductModel)
        await self.db.commit()
        
        # Update category ProductModel counts
        if category_ids:
            await self._update_category_product_counts(category_ids, increment=False)
        
        # Update brand ProductModel count
        if brand_id:
            await self._update_brand_product_count(brand_id, increment=False)
        
        # Clear cache
        if self.cache:
            await self.cache.delete_product(product_id)
    
    async def search_products(
        self,
        search_params: ProductSearch,
        pagination: PaginationParams
    ) -> PaginatedResponse[Product]:
        """Search products with filters and pagination.
        
        Args:
            search_params: Search and filter parameters
            pagination: Pagination parameters
            
        Returns:
            Paginated response with products
        """
        # Build base query
        query = select(ProductModel).options(
            selectinload(ProductModel.categories),
            selectinload(ProductModel.brand),
            selectinload(ProductModel.images)
        )
        
        # Apply filters
        conditions = []
        
        # Text search
        if search_params.query:
            search_term = f"%{search_params.query}%"
            conditions.append(
                or_(
                    ProductModel.name.ilike(search_term),
                    ProductModel.description.ilike(search_term),
                    ProductModel.short_description.ilike(search_term),
                    ProductModel.sku.ilike(search_term),
                    ProductModel.tags.contains([search_params.query.lower()])
                )
            )
        
        # Category filter
        if search_params.category_ids:
            conditions.append(ProductModel.categories.any(Category.id.in_(search_params.category_ids)))
        
        # Brand filter
        if search_params.brand_ids:
            conditions.append(ProductModel.brand_id.in_(search_params.brand_ids))
        
        # Price range filter
        if search_params.min_price is not None:
            conditions.append(ProductModel.price >= search_params.min_price)
        if search_params.max_price is not None:
            conditions.append(ProductModel.price <= search_params.max_price)
        
        # Stock filter
        if search_params.in_stock_only:
            conditions.append(ProductModel.stock_quantity > 0)
        
        # Featured filter
        if search_params.featured_only:
            conditions.append(ProductModel.is_featured == True)
        
        # Status filter
        if search_params.status:
            conditions.append(ProductModel.status == search_params.status)
        
        # Tags filter
        if search_params.tags:
            for tag in search_params.tags:
                conditions.append(ProductModel.tags.contains([tag.lower()]))
        
        # Attributes filter
        if search_params.attributes:
            for key, value in search_params.attributes.items():
                conditions.append(ProductModel.attributes[key].astext == value)
        
        # Apply conditions
        if conditions:
            query = query.where(and_(*conditions))
        
        # Apply sorting
        sort_column = getattr(ProductModel, search_params.sort_by, ProductModel.created_at)
        if search_params.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.offset(pagination.skip).limit(pagination.limit)
        
        # Execute query
        result = await self.db.execute(query)
        products = result.scalars().all()
        
        return PaginatedResponse(
            items=list(products),
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=pagination.get_total_pages(total)
        )
    
    async def get_featured_products(self, limit: int = 10) -> List[ProductModel]:
        """Get featured products.
        
        Args:
            limit: Maximum number of products to return
            
        Returns:
            List of featured products
        """
        # Try cache first
        if self.cache:
            cached_products = await self.cache.get_featured_products()
            if cached_products:
                return cached_products[:limit]
        
        # Query database
        result = await self.db.execute(
            select(ProductModel)
            .options(
                selectinload(ProductModel.categories),
                selectinload(ProductModel.brand),
                selectinload(ProductModel.images)
            )
            .where(
                and_(
                    ProductModel.is_featured == True,
                    ProductModel.status == ProductStatus.ACTIVE
                )
            )
            .order_by(desc(ProductModel.rating), desc(ProductModel.created_at))
            .limit(limit)
        )
        products = result.scalars().all()
        
        # Cache products
        if self.cache and products:
            await self.cache.set_featured_products(list(products))
        
        return list(products)
    
    async def get_related_products(self, product_id: str, limit: int = 5) -> List[ProductModel]:
        """Get products related to a given ProductModel.
        
        Args:
            product_id: ProductModel ID
            limit: Maximum number of related products
            
        Returns:
            List of related products
        """
        ProductModel = await self.get_product(product_id, increment_view=False)
        if not ProductModel:
            return []
        
        # Get products from same categories or brand
        category_ids = [str(cat.id) for cat in ProductModel.categories]
        
        conditions = [ProductModel.id != product_id, ProductModel.status == ProductStatus.ACTIVE]
        
        if category_ids:
            conditions.append(ProductModel.categories.any(Category.id.in_(category_ids)))
        elif ProductModel.brand_id:
            conditions.append(ProductModel.brand_id == ProductModel.brand_id)
        
        result = await self.db.execute(
            select(ProductModel)
            .options(
                selectinload(ProductModel.categories),
                selectinload(ProductModel.brand),
                selectinload(ProductModel.images)
            )
            .where(and_(*conditions))
            .order_by(desc(ProductModel.rating), desc(ProductModel.view_count))
            .limit(limit)
        )
        
        return list(result.scalars().all())
    
    async def update_stock(self, product_id: str, quantity: int, operation: str = "set") -> ProductModel:
        """Update ProductModel stock quantity.
        
        Args:
            product_id: ProductModel ID
            quantity: Quantity to set/add/subtract
            operation: Operation type (set, add, subtract)
            
        Returns:
            Updated product
            
        Raises:
            HTTPException: If ProductModel not found or invalid operation
        """
        ProductModel = await self.get_product(product_id, increment_view=False)
        if not ProductModel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ProductModel not found"
            )
        
        if operation == "set":
            new_quantity = quantity
        elif operation == "add":
            new_quantity = ProductModel.stock_quantity + quantity
        elif operation == "subtract":
            new_quantity = ProductModel.stock_quantity - quantity
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid operation. Use 'set', 'add', or 'subtract'"
            )
        
        if new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock quantity cannot be negative"
            )
        
        await self.db.execute(
            update(ProductModel)
            .where(ProductModel.id == product_id)
            .values(stock_quantity=new_quantity)
        )
        await self.db.commit()
        
        # Clear cache
        if self.cache:
            await self.cache.delete_product(product_id)
        
        return await self.get_product(product_id, increment_view=False)
    
    async def bulk_operation(self, operation_data: ProductBulkOperation) -> Dict[str, int]:
        """Perform bulk operations on products.
        
        Args:
            operation_data: Bulk operation data
            
        Returns:
            Dictionary with operation results
        """
        operation = operation_data.operation
        product_ids = operation_data.product_ids
        data = operation_data.data or {}
        
        # Verify products exist
        result = await self.db.execute(
            select(func.count()).where(ProductModel.id.in_(product_ids))
        )
        existing_count = result.scalar()
        
        if existing_count != len(product_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some products not found"
            )
        
        # Perform operation
        if operation == "activate":
            await self.db.execute(
                update(ProductModel)
                .where(ProductModel.id.in_(product_ids))
                .values(status=ProductStatus.ACTIVE)
            )
        elif operation == "deactivate":
            await self.db.execute(
                update(ProductModel)
                .where(ProductModel.id.in_(product_ids))
                .values(status=ProductStatus.INACTIVE)
            )
        elif operation == "feature":
            await self.db.execute(
                update(ProductModel)
                .where(ProductModel.id.in_(product_ids))
                .values(is_featured=True)
            )
        elif operation == "unfeature":
            await self.db.execute(
                update(ProductModel)
                .where(ProductModel.id.in_(product_ids))
                .values(is_featured=False)
            )
        elif operation == "update_stock":
            stock_quantity = data.get("stock_quantity")
            if stock_quantity is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="stock_quantity required for update_stock operation"
                )
            await self.db.execute(
                update(ProductModel)
                .where(ProductModel.id.in_(product_ids))
                .values(stock_quantity=stock_quantity)
            )
        elif operation == "update_price":
            price = data.get("price")
            if price is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="price required for update_price operation"
                )
            await self.db.execute(
                update(ProductModel)
                .where(ProductModel.id.in_(product_ids))
                .values(price=price)
            )
        elif operation == "delete":
            # Get category and brand info before deletion
            products_info = await self.db.execute(
                select(ProductModel.id, ProductModel.brand_id)
                .options(selectinload(ProductModel.categories))
                .where(ProductModel.id.in_(product_ids))
            )
            
            # Delete products
            await self.db.execute(
                ProductModel.__table__.delete().where(ProductModel.id.in_(product_ids))
            )
        
        await self.db.commit()
        
        # Clear cache for affected products
        if self.cache:
            for product_id in product_ids:
                await self.cache.delete_product(product_id)
        
        return {
            "operation": operation,
            "affected_count": len(product_ids),
            "success": True
        }
    
    async def get_product_stats(self, product_id: str) -> ProductStats:
        """Get ProductModel statistics.
        
        Args:
            product_id: ProductModel ID
            
        Returns:
            ProductModel statistics
            
        Raises:
            HTTPException: If ProductModel not found
        """
        ProductModel = await self.get_product(product_id, increment_view=False)
        if not ProductModel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ProductModel not found"
            )
        
        # Calculate derived metrics
        revenue = ProductModel.price * ProductModel.sales_count
        profit = None
        profit_margin = None
        
        if ProductModel.cost_price:
            profit = (ProductModel.price - ProductModel.cost_price) * ProductModel.sales_count
            profit_margin = ((ProductModel.price - ProductModel.cost_price) / ProductModel.price) * 100
        
        conversion_rate = 0.0
        if ProductModel.view_count > 0:
            conversion_rate = (ProductModel.sales_count / ProductModel.view_count) * 100
        
        return ProductStats(
            id=str(ProductModel.id),
            name=ProductModel.name,
            view_count=ProductModel.view_count,
            sales_count=ProductModel.sales_count,
            revenue=revenue,
            rating=ProductModel.rating,
            review_count=ProductModel.review_count,
            conversion_rate=conversion_rate,
            profit=profit,
            profit_margin=profit_margin
        )
    
    async def _get_product_by_sku(self, sku: str) -> Optional[ProductModel]:
        """Get ProductModel by SKU.
        
        Args:
            sku: ProductModel SKU
            
        Returns:
            ProductModel object or None if not found
        """
        result = await self.db.execute(
            select(ProductModel).where(ProductModel.sku == sku.upper())
        )
        return result.scalar_one_or_none()
    
    async def _validate_categories(self, category_ids: List[str]) -> List[Category]:
        """Validate that categories exist.
        
        Args:
            category_ids: List of category IDs
            
        Returns:
            List of category objects
            
        Raises:
            HTTPException: If any category not found
        """
        result = await self.db.execute(
            select(Category).where(Category.id.in_(category_ids))
        )
        categories = result.scalars().all()
        
        if len(categories) != len(category_ids):
            found_ids = {str(cat.id) for cat in categories}
            missing_ids = set(category_ids) - found_ids
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Categories not found: {', '.join(missing_ids)}"
            )
        
        return list(categories)
    
    async def _validate_brand(self, brand_id: str) -> Brand:
        """Validate that brand exists.
        
        Args:
            brand_id: Brand ID
            
        Returns:
            Brand object
            
        Raises:
            HTTPException: If brand not found
        """
        result = await self.db.execute(
            select(Brand).where(Brand.id == brand_id)
        )
        brand = result.scalar_one_or_none()
        
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Brand not found: {brand_id}"
            )
        
        return brand
    
    async def _increment_view_count(self, product_id: str) -> None:
        """Increment ProductModel view count.
        
        Args:
            product_id: ProductModel ID
        """
        await self.db.execute(
            update(ProductModel)
            .where(ProductModel.id == product_id)
            .values(view_count=ProductModel.view_count + 1)
        )
        await self.db.commit()
    
    async def _update_category_product_counts(self, category_ids: List[str], increment: bool = True) -> None:
        """Update ProductModel counts for categories.
        
        Args:
            category_ids: List of category IDs
            increment: Whether to increment (True) or decrement (False)
        """
        if increment:
            await self.db.execute(
                update(Category)
                .where(Category.id.in_(category_ids))
                .values(product_count=Category.product_count + 1)
            )
        else:
            await self.db.execute(
                update(Category)
                .where(Category.id.in_(category_ids))
                .values(product_count=func.greatest(Category.product_count - 1, 0))
            )
        await self.db.commit()
    
    async def _update_brand_product_count(self, brand_id: str, increment: bool = True) -> None:
        """Update ProductModel count for brand.
        
        Args:
            brand_id: Brand ID
            increment: Whether to increment (True) or decrement (False)
        """
        if increment:
            await self.db.execute(
                update(Brand)
                .where(Brand.id == brand_id)
                .values(product_count=Brand.product_count + 1)
            )
        else:
            await self.db.execute(
                update(Brand)
                .where(Brand.id == brand_id)
                .values(product_count=func.greatest(Brand.product_count - 1, 0))
            )
        await self.db.commit()
