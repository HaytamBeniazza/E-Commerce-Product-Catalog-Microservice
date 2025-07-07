"""Brand service for managing brand operations.

This module provides functionality for brand CRUD operations,
brand analytics, and brand management.
"""

from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.brand import Brand
from app.schemas.brand import (
    BrandCreate,
    BrandUpdate,
    BrandBulkOperation,
    BrandStats,
    BrandComparison
)
from app.schemas.common import PaginationParams, PaginatedResponse
from app.services.cache_service import CacheService


class BrandService:
    """Service for managing brand operations."""
    
    def __init__(self, db_session: AsyncSession, cache_service: Optional[CacheService] = None):
        """Initialize brand service.
        
        Args:
            db_session: Database session
            cache_service: Cache service for storing brand data
        """
        self.db = db_session
        self.cache = cache_service
    
    async def create_brand(self, brand_data: BrandCreate, user_id: str) -> Brand:
        """Create a new brand.
        
        Args:
            brand_data: Brand creation data
            user_id: ID of user creating the brand
            
        Returns:
            Created brand object
            
        Raises:
            HTTPException: If brand name already exists
        """
        # Check if brand name already exists
        existing_brand = await self._get_brand_by_name(brand_data.name)
        if existing_brand:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Brand with name '{brand_data.name}' already exists"
            )
        
        # Create brand
        brand = Brand(
            name=brand_data.name,
            description=brand_data.description,
            website=str(brand_data.website) if brand_data.website else None,
            email=brand_data.email,
            phone=brand_data.phone,
            logo_url=brand_data.logo_url,
            banner_url=brand_data.banner_url,
            company_name=brand_data.company_name,
            founded_year=brand_data.founded_year,
            country=brand_data.country,
            meta_title=brand_data.meta_title,
            meta_description=brand_data.meta_description,
            meta_keywords=brand_data.meta_keywords,
            display_order=brand_data.display_order,
            is_active=brand_data.is_active,
            is_featured=brand_data.is_featured,
            is_verified=brand_data.is_verified,
            social_media=brand_data.social_media or {},
            created_by=user_id
        )
        
        self.db.add(brand)
        await self.db.commit()
        await self.db.refresh(brand)
        
        # Cache brand
        if self.cache:
            await self.cache.set_brand(brand)
        
        return brand
    
    async def get_brand(self, brand_id: str, increment_view: bool = False) -> Optional[Brand]:
        """Get brand by ID.
        
        Args:
            brand_id: Brand ID
            increment_view: Whether to increment view count
            
        Returns:
            Brand object or None if not found
        """
        # Try cache first
        if self.cache:
            cached_brand = await self.cache.get_brand(brand_id)
            if cached_brand:
                if increment_view:
                    await self._increment_view_count(brand_id)
                return cached_brand
        
        # Query database
        result = await self.db.execute(
            select(Brand).where(Brand.id == brand_id)
        )
        brand = result.scalar_one_or_none()
        
        if brand:
            # Cache brand
            if self.cache:
                await self.cache.set_brand(brand)
            
            # Increment view count
            if increment_view:
                await self._increment_view_count(brand_id)
        
        return brand
    
    async def get_brand_by_slug(self, slug: str, increment_view: bool = False) -> Optional[Brand]:
        """Get brand by slug.
        
        Args:
            slug: Brand slug
            increment_view: Whether to increment view count
            
        Returns:
            Brand object or None if not found
        """
        result = await self.db.execute(
            select(Brand).where(Brand.slug == slug)
        )
        brand = result.scalar_one_or_none()
        
        if brand and increment_view:
            await self._increment_view_count(str(brand.id))
        
        return brand
    
    async def update_brand(self, brand_id: str, brand_data: BrandUpdate, user_id: str) -> Brand:
        """Update an existing brand.
        
        Args:
            brand_id: Brand ID
            brand_data: Brand update data
            user_id: ID of user updating the brand
            
        Returns:
            Updated brand object
            
        Raises:
            HTTPException: If brand not found or name conflict
        """
        # Get existing brand
        brand = await self.get_brand(brand_id)
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand not found"
            )
        
        # Check name conflict if name is being updated
        if brand_data.name and brand_data.name != brand.name:
            existing_brand = await self._get_brand_by_name(brand_data.name)
            if existing_brand and existing_brand.id != brand.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Brand with name '{brand_data.name}' already exists"
                )
        
        # Update brand fields
        update_data = brand_data.dict(exclude_unset=True)
        update_data['updated_by'] = user_id
        
        # Handle website URL conversion
        if 'website' in update_data and update_data['website']:
            update_data['website'] = str(update_data['website'])
        
        for field, value in update_data.items():
            setattr(brand, field, value)
        
        await self.db.commit()
        await self.db.refresh(brand)
        
        # Clear cache
        if self.cache:
            await self.cache.delete_brand(brand_id)
        
        return brand
    
    async def delete_brand(self, brand_id: str, force: bool = False) -> None:
        """Delete a brand.
        
        Args:
            brand_id: Brand ID
            force: Whether to force delete even if brand has products
            
        Raises:
            HTTPException: If brand not found or has dependencies
        """
        brand = await self.get_brand(brand_id)
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand not found"
            )
        
        # Check for products
        if brand.product_count > 0 and not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete brand with products. Use force=true or remove products first."
            )
        
        # If force delete, update products to remove brand reference
        if force and brand.product_count > 0:
            from app.models.product import Product
            await self.db.execute(
                update(Product)
                .where(Product.brand_id == brand_id)
                .values(brand_id=None)
            )
        
        # Delete brand
        await self.db.delete(brand)
        await self.db.commit()
        
        # Clear cache
        if self.cache:
            await self.cache.delete_brand(brand_id)
    
    async def get_brands(
        self,
        active_only: bool = True,
        featured_only: bool = False,
        verified_only: bool = False,
        search_query: Optional[str] = None,
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResponse[Brand] | List[Brand]:
        """Get brands with optional filtering and pagination.
        
        Args:
            active_only: Whether to return only active brands
            featured_only: Whether to return only featured brands
            verified_only: Whether to return only verified brands
            search_query: Search query for brand name or description
            pagination: Pagination parameters
            
        Returns:
            Paginated response or list of brands
        """
        # Build query
        query = select(Brand)
        
        # Apply filters
        conditions = []
        
        if active_only:
            conditions.append(Brand.is_active == True)
        
        if featured_only:
            conditions.append(Brand.is_featured == True)
        
        if verified_only:
            conditions.append(Brand.is_verified == True)
        
        if search_query:
            search_term = f"%{search_query}%"
            conditions.append(
                Brand.name.ilike(search_term) | 
                Brand.description.ilike(search_term) |
                Brand.company_name.ilike(search_term)
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Apply ordering
        query = query.order_by(Brand.display_order, desc(Brand.rating), Brand.name)
        
        # Handle pagination
        if pagination:
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()
            
            # Apply pagination
            query = query.offset(pagination.skip).limit(pagination.limit)
            
            # Execute query
            result = await self.db.execute(query)
            brands = result.scalars().all()
            
            return PaginatedResponse(
                items=list(brands),
                total=total,
                page=pagination.page,
                size=pagination.size,
                pages=pagination.get_total_pages(total)
            )
        else:
            # Execute query without pagination
            result = await self.db.execute(query)
            return list(result.scalars().all())
    
    async def get_featured_brands(self, limit: int = 10) -> List[Brand]:
        """Get featured brands.
        
        Args:
            limit: Maximum number of brands to return
            
        Returns:
            List of featured brands
        """
        # Try cache first
        if self.cache:
            cached_brands = await self.cache.get_featured_brands()
            if cached_brands:
                return cached_brands[:limit]
        
        # Query database
        result = await self.db.execute(
            select(Brand)
            .where(
                and_(
                    Brand.is_featured == True,
                    Brand.is_active == True
                )
            )
            .order_by(Brand.display_order, desc(Brand.rating), desc(Brand.product_count))
            .limit(limit)
        )
        brands = result.scalars().all()
        
        # Cache brands
        if self.cache and brands:
            await self.cache.set_featured_brands(list(brands))
        
        return list(brands)
    
    async def get_top_brands(self, limit: int = 10, metric: str = "product_count") -> List[Brand]:
        """Get top brands by specified metric.
        
        Args:
            limit: Maximum number of brands to return
            metric: Metric to sort by (product_count, rating, view_count)
            
        Returns:
            List of top brands
        """
        # Validate metric
        valid_metrics = ["product_count", "rating", "view_count", "review_count"]
        if metric not in valid_metrics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid metric. Must be one of: {', '.join(valid_metrics)}"
            )
        
        # Build query
        sort_column = getattr(Brand, metric)
        
        result = await self.db.execute(
            select(Brand)
            .where(Brand.is_active == True)
            .order_by(desc(sort_column), Brand.name)
            .limit(limit)
        )
        
        return list(result.scalars().all())
    
    async def bulk_operation(self, operation_data: BrandBulkOperation) -> Dict[str, int]:
        """Perform bulk operations on brands.
        
        Args:
            operation_data: Bulk operation data
            
        Returns:
            Dictionary with operation results
        """
        operation = operation_data.operation
        brand_ids = operation_data.brand_ids
        
        # Verify brands exist
        result = await self.db.execute(
            select(func.count()).where(Brand.id.in_(brand_ids))
        )
        existing_count = result.scalar()
        
        if existing_count != len(brand_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some brands not found"
            )
        
        # Perform operation
        if operation == "activate":
            await self.db.execute(
                update(Brand)
                .where(Brand.id.in_(brand_ids))
                .values(is_active=True)
            )
        elif operation == "deactivate":
            await self.db.execute(
                update(Brand)
                .where(Brand.id.in_(brand_ids))
                .values(is_active=False)
            )
        elif operation == "feature":
            await self.db.execute(
                update(Brand)
                .where(Brand.id.in_(brand_ids))
                .values(is_featured=True)
            )
        elif operation == "unfeature":
            await self.db.execute(
                update(Brand)
                .where(Brand.id.in_(brand_ids))
                .values(is_featured=False)
            )
        elif operation == "verify":
            await self.db.execute(
                update(Brand)
                .where(Brand.id.in_(brand_ids))
                .values(is_verified=True)
            )
        elif operation == "unverify":
            await self.db.execute(
                update(Brand)
                .where(Brand.id.in_(brand_ids))
                .values(is_verified=False)
            )
        elif operation == "delete":
            # Check for dependencies
            brands_with_products = await self.db.execute(
                select(func.count())
                .where(
                    and_(
                        Brand.id.in_(brand_ids),
                        Brand.product_count > 0
                    )
                )
            )
            
            if brands_with_products.scalar() > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete brands that have products"
                )
            
            # Delete brands
            await self.db.execute(
                Brand.__table__.delete().where(Brand.id.in_(brand_ids))
            )
        
        await self.db.commit()
        
        # Clear cache for affected brands
        if self.cache:
            for brand_id in brand_ids:
                await self.cache.delete_brand(brand_id)
        
        return {
            "operation": operation,
            "affected_count": len(brand_ids),
            "success": True
        }
    
    async def get_brand_stats(self, brand_id: str) -> BrandStats:
        """Get brand statistics.
        
        Args:
            brand_id: Brand ID
            
        Returns:
            Brand statistics
            
        Raises:
            HTTPException: If brand not found
        """
        brand = await self.get_brand(brand_id)
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand not found"
            )
        
        # Get product statistics for this brand
        from app.models.product import Product, ProductStatus
        
        # Count active products
        active_count_result = await self.db.execute(
            select(func.count())
            .where(
                and_(
                    Product.brand_id == brand_id,
                    Product.status == ProductStatus.ACTIVE
                )
            )
        )
        active_product_count = active_count_result.scalar()
        
        # Get price statistics
        price_stats_result = await self.db.execute(
            select(
                func.avg(Product.price),
                func.min(Product.price),
                func.max(Product.price),
                func.sum(Product.price * Product.sales_count)
            )
            .where(
                and_(
                    Product.brand_id == brand_id,
                    Product.status == ProductStatus.ACTIVE
                )
            )
        )
        price_stats = price_stats_result.first()
        
        # Calculate market share (simplified - based on product count)
        total_products_result = await self.db.execute(
            select(func.count())
            .where(Product.status == ProductStatus.ACTIVE)
        )
        total_products = total_products_result.scalar()
        market_share = (brand.product_count / total_products * 100) if total_products > 0 else 0
        
        return BrandStats(
            id=str(brand.id),
            name=brand.name,
            product_count=brand.product_count,
            active_product_count=active_product_count,
            view_count=brand.view_count,
            rating=brand.rating,
            review_count=brand.review_count,
            avg_product_price=price_stats[0],
            min_product_price=price_stats[1],
            max_product_price=price_stats[2],
            total_revenue=price_stats[3],
            market_share=market_share
        )
    
    async def compare_brands(self, brand_ids: List[str]) -> BrandComparison:
        """Compare multiple brands.
        
        Args:
            brand_ids: List of brand IDs to compare
            
        Returns:
            Brand comparison data
            
        Raises:
            HTTPException: If any brand not found
        """
        if len(brand_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 brands required for comparison"
            )
        
        if len(brand_ids) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 5 brands allowed for comparison"
            )
        
        # Get brand statistics for all brands
        brand_stats = []
        for brand_id in brand_ids:
            stats = await self.get_brand_stats(brand_id)
            brand_stats.append(stats)
        
        # Build comparison metrics
        comparison_metrics = {
            "product_count": {stats.name: stats.product_count for stats in brand_stats},
            "rating": {stats.name: stats.rating for stats in brand_stats},
            "view_count": {stats.name: stats.view_count for stats in brand_stats},
            "review_count": {stats.name: stats.review_count for stats in brand_stats},
            "market_share": {stats.name: stats.market_share for stats in brand_stats if stats.market_share}
        }
        
        # Add price metrics if available
        avg_prices = {stats.name: stats.avg_product_price for stats in brand_stats if stats.avg_product_price}
        if avg_prices:
            comparison_metrics["avg_product_price"] = avg_prices
        
        total_revenues = {stats.name: stats.total_revenue for stats in brand_stats if stats.total_revenue}
        if total_revenues:
            comparison_metrics["total_revenue"] = total_revenues
        
        return BrandComparison(
            brands=brand_stats,
            comparison_metrics=comparison_metrics
        )
    
    async def update_brand_rating(self, brand_id: str, new_rating: float, review_count_delta: int = 1) -> None:
        """Update brand rating and review count.
        
        Args:
            brand_id: Brand ID
            new_rating: New rating to incorporate
            review_count_delta: Change in review count (default: 1)
        """
        brand = await self.get_brand(brand_id)
        if not brand:
            return
        
        # Calculate new average rating
        current_total = brand.rating * brand.review_count
        new_total = current_total + new_rating
        new_review_count = brand.review_count + review_count_delta
        new_avg_rating = new_total / new_review_count if new_review_count > 0 else 0
        
        # Update brand
        await self.db.execute(
            update(Brand)
            .where(Brand.id == brand_id)
            .values(
                rating=new_avg_rating,
                review_count=new_review_count
            )
        )
        await self.db.commit()
        
        # Clear cache
        if self.cache:
            await self.cache.delete_brand(brand_id)
    
    async def _get_brand_by_name(self, name: str) -> Optional[Brand]:
        """Get brand by name.
        
        Args:
            name: Brand name
            
        Returns:
            Brand object or None if not found
        """
        result = await self.db.execute(
            select(Brand).where(Brand.name.ilike(name))
        )
        return result.scalar_one_or_none()
    
    async def _increment_view_count(self, brand_id: str) -> None:
        """Increment brand view count.
        
        Args:
            brand_id: Brand ID
        """
        await self.db.execute(
            update(Brand)
            .where(Brand.id == brand_id)
            .values(view_count=Brand.view_count + 1)
        )
        await self.db.commit()