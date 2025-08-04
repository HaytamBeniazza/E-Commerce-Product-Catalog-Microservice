"""BrandModel service for managing BrandModel operations.

This module provides functionality for BrandModel CRUD operations,
brand analytics, and BrandModel management.
"""

from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.brand import Brand as BrandModel
from app.schemas.brand import (
    Brand,
    BrandCreate,
    BrandUpdate,
    BrandBulkOperation,
    BrandStats,
    BrandComparison
)
from app.schemas.common import PaginationParams, PaginatedResponse
from app.services.cache_service import CacheService


class BrandService:
    """Service for managing BrandModel operations."""
    
    def __init__(self, db_session: AsyncSession, cache_service: Optional[CacheService] = None):
        """Initialize BrandModel service.
        
        Args:
            db_session: Database session
            cache_service: Cache service for storing BrandModel data
        """
        self.db = db_session
        self.cache = cache_service
    
    async def create_brand(self, brand_data: BrandCreate, user_id: str) -> BrandModel:
        """Create a new BrandModel.
        
        Args:
            brand_data: BrandModel creation data
            user_id: ID of user creating the brand
            
        Returns:
            Created BrandModel object
            
        Raises:
            HTTPException: If BrandModel name already exists
        """
        # Check if BrandModel name already exists
        existing_brand = await self._get_brand_by_name(brand_data.name)
        if existing_brand:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"BrandModel with name '{brand_data.name}' already exists"
            )
        
        # Create brand
        BrandModel = BrandModel(
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
        
        self.db.add(BrandModel)
        await self.db.commit()
        await self.db.refresh(BrandModel)
        
        # Cache brand
        if self.cache:
            await self.cache.set_brand(BrandModel)
        
        return brand
    
    async def get_brand(self, brand_id: str, increment_view: bool = False) -> Optional[BrandModel]:
        """Get BrandModel by ID.
        
        Args:
            brand_id: BrandModel ID
            increment_view: Whether to increment view count
            
        Returns:
            BrandModel object or None if not found
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
            select(BrandModel).where(BrandModel.id == brand_id)
        )
        BrandModel = result.scalar_one_or_none()
        
        if BrandModel:
            # Cache brand
            if self.cache:
                await self.cache.set_brand(BrandModel)
            
            # Increment view count
            if increment_view:
                await self._increment_view_count(brand_id)
        
        return brand
    
    async def get_brand_by_slug(self, slug: str, increment_view: bool = False) -> Optional[BrandModel]:
        """Get BrandModel by slug.
        
        Args:
            slug: BrandModel slug
            increment_view: Whether to increment view count
            
        Returns:
            BrandModel object or None if not found
        """
        result = await self.db.execute(
            select(BrandModel).where(BrandModel.slug == slug)
        )
        BrandModel = result.scalar_one_or_none()
        
        if BrandModel and increment_view:
            await self._increment_view_count(str(BrandModel.id))
        
        return brand
    
    async def update_brand(self, brand_id: str, brand_data: BrandUpdate, user_id: str) -> BrandModel:
        """Update an existing BrandModel.
        
        Args:
            brand_id: BrandModel ID
            brand_data: BrandModel update data
            user_id: ID of user updating the brand
            
        Returns:
            Updated BrandModel object
            
        Raises:
            HTTPException: If BrandModel not found or name conflict
        """
        # Get existing brand
        BrandModel = await self.get_brand(brand_id)
        if not BrandModel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BrandModel not found"
            )
        
        # Check name conflict if name is being updated
        if brand_data.name and brand_data.name != BrandModel.name:
            existing_brand = await self._get_brand_by_name(brand_data.name)
            if existing_brand and existing_brand.id != BrandModel.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"BrandModel with name '{brand_data.name}' already exists"
                )
        
        # Update BrandModel fields
        update_data = brand_data.dict(exclude_unset=True)
        update_data['updated_by'] = user_id
        
        # Handle website URL conversion
        if 'website' in update_data and update_data['website']:
            update_data['website'] = str(update_data['website'])
        
        for field, value in update_data.items():
            setattr(BrandModel, field, value)
        
        await self.db.commit()
        await self.db.refresh(BrandModel)
        
        # Clear cache
        if self.cache:
            await self.cache.delete_brand(brand_id)
        
        return brand
    
    async def delete_brand(self, brand_id: str, force: bool = False) -> None:
        """Delete a BrandModel.
        
        Args:
            brand_id: BrandModel ID
            force: Whether to force delete even if BrandModel has products
            
        Raises:
            HTTPException: If BrandModel not found or has dependencies
        """
        BrandModel = await self.get_brand(brand_id)
        if not BrandModel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BrandModel not found"
            )
        
        # Check for products
        if BrandModel.product_count > 0 and not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete BrandModel with products. Use force=true or remove products first."
            )
        
        # If force delete, update products to remove BrandModel reference
        if force and BrandModel.product_count > 0:
            from app.models.product import Product
            await self.db.execute(
                update(Product)
                .where(Product.brand_id == brand_id)
                .values(brand_id=None)
            )
        
        # Delete brand
        await self.db.delete(BrandModel)
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
            search_query: Search query for BrandModel name or description
            pagination: Pagination parameters
            
        Returns:
            Paginated response or list of brands
        """
        # Build query
        query = select(BrandModel)
        
        # Apply filters
        conditions = []
        
        if active_only:
            conditions.append(BrandModel.is_active == True)
        
        if featured_only:
            conditions.append(BrandModel.is_featured == True)
        
        if verified_only:
            conditions.append(BrandModel.is_verified == True)
        
        if search_query:
            search_term = f"%{search_query}%"
            conditions.append(
                BrandModel.name.ilike(search_term) | 
                BrandModel.description.ilike(search_term) |
                BrandModel.company_name.ilike(search_term)
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Apply ordering
        query = query.order_by(BrandModel.display_order, desc(BrandModel.rating), BrandModel.name)
        
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
    
    async def get_featured_brands(self, limit: int = 10) -> List[BrandModel]:
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
            select(BrandModel)
            .where(
                and_(
                    BrandModel.is_featured == True,
                    BrandModel.is_active == True
                )
            )
            .order_by(BrandModel.display_order, desc(BrandModel.rating), desc(BrandModel.product_count))
            .limit(limit)
        )
        brands = result.scalars().all()
        
        # Cache brands
        if self.cache and brands:
            await self.cache.set_featured_brands(list(brands))
        
        return list(brands)
    
    async def get_top_brands(self, limit: int = 10, metric: str = "product_count") -> List[BrandModel]:
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
        sort_column = getattr(BrandModel, metric)
        
        result = await self.db.execute(
            select(BrandModel)
            .where(BrandModel.is_active == True)
            .order_by(desc(sort_column), BrandModel.name)
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
            select(func.count()).where(BrandModel.id.in_(brand_ids))
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
                update(BrandModel)
                .where(BrandModel.id.in_(brand_ids))
                .values(is_active=True)
            )
        elif operation == "deactivate":
            await self.db.execute(
                update(BrandModel)
                .where(BrandModel.id.in_(brand_ids))
                .values(is_active=False)
            )
        elif operation == "feature":
            await self.db.execute(
                update(BrandModel)
                .where(BrandModel.id.in_(brand_ids))
                .values(is_featured=True)
            )
        elif operation == "unfeature":
            await self.db.execute(
                update(BrandModel)
                .where(BrandModel.id.in_(brand_ids))
                .values(is_featured=False)
            )
        elif operation == "verify":
            await self.db.execute(
                update(BrandModel)
                .where(BrandModel.id.in_(brand_ids))
                .values(is_verified=True)
            )
        elif operation == "unverify":
            await self.db.execute(
                update(BrandModel)
                .where(BrandModel.id.in_(brand_ids))
                .values(is_verified=False)
            )
        elif operation == "delete":
            # Check for dependencies
            brands_with_products = await self.db.execute(
                select(func.count())
                .where(
                    and_(
                        BrandModel.id.in_(brand_ids),
                        BrandModel.product_count > 0
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
                BrandModel.__table__.delete().where(BrandModel.id.in_(brand_ids))
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
        """Get BrandModel statistics.
        
        Args:
            brand_id: BrandModel ID
            
        Returns:
            BrandModel statistics
            
        Raises:
            HTTPException: If BrandModel not found
        """
        BrandModel = await self.get_brand(brand_id)
        if not BrandModel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BrandModel not found"
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
        market_share = (BrandModel.product_count / total_products * 100) if total_products > 0 else 0
        
        return BrandStats(
            id=str(BrandModel.id),
            name=BrandModel.name,
            product_count=BrandModel.product_count,
            active_product_count=active_product_count,
            view_count=BrandModel.view_count,
            rating=BrandModel.rating,
            review_count=BrandModel.review_count,
            avg_product_price=price_stats[0],
            min_product_price=price_stats[1],
            max_product_price=price_stats[2],
            total_revenue=price_stats[3],
            market_share=market_share
        )
    
    async def compare_brands(self, brand_ids: List[str]) -> BrandComparison:
        """Compare multiple brands.
        
        Args:
            brand_ids: List of BrandModel IDs to compare
            
        Returns:
            BrandModel comparison data
            
        Raises:
            HTTPException: If any BrandModel not found
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
        
        # Get BrandModel statistics for all brands
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
        """Update BrandModel rating and review count.
        
        Args:
            brand_id: BrandModel ID
            new_rating: New rating to incorporate
            review_count_delta: Change in review count (default: 1)
        """
        BrandModel = await self.get_brand(brand_id)
        if not BrandModel:
            return
        
        # Calculate new average rating
        current_total = BrandModel.rating * BrandModel.review_count
        new_total = current_total + new_rating
        new_review_count = BrandModel.review_count + review_count_delta
        new_avg_rating = new_total / new_review_count if new_review_count > 0 else 0
        
        # Update brand
        await self.db.execute(
            update(BrandModel)
            .where(BrandModel.id == brand_id)
            .values(
                rating=new_avg_rating,
                review_count=new_review_count
            )
        )
        await self.db.commit()
        
        # Clear cache
        if self.cache:
            await self.cache.delete_brand(brand_id)
    
    async def _get_brand_by_name(self, name: str) -> Optional[BrandModel]:
        """Get BrandModel by name.
        
        Args:
            name: BrandModel name
            
        Returns:
            BrandModel object or None if not found
        """
        result = await self.db.execute(
            select(BrandModel).where(BrandModel.name.ilike(name))
        )
        return result.scalar_one_or_none()
    
    async def _increment_view_count(self, brand_id: str) -> None:
        """Increment BrandModel view count.
        
        Args:
            brand_id: BrandModel ID
        """
        await self.db.execute(
            update(BrandModel)
            .where(BrandModel.id == brand_id)
            .values(view_count=BrandModel.view_count + 1)
        )
        await self.db.commit()
