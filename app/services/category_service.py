"""Category service for managing category operations.

This module provides functionality for category CRUD operations,
hierarchy management, and category analytics.
"""

from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryMove,
    CategoryBulkOperation,
    CategoryStats,
    CategoryTree,
    CategoryWithChildren
)
from app.schemas.common import PaginationParams, PaginatedResponse
from app.services.cache_service import CacheService


class CategoryService:
    """Service for managing category operations."""
    
    def __init__(self, db_session: AsyncSession, cache_service: Optional[CacheService] = None):
        """Initialize category service.
        
        Args:
            db_session: Database session
            cache_service: Cache service for storing category data
        """
        self.db = db_session
        self.cache = cache_service
    
    async def create_category(self, category_data: CategoryCreate, user_id: str) -> Category:
        """Create a new category.
        
        Args:
            category_data: Category creation data
            user_id: ID of user creating the category
            
        Returns:
            Created category object
            
        Raises:
            HTTPException: If parent category not found or circular reference detected
        """
        # Validate parent category if provided
        parent_category = None
        if category_data.parent_id:
            parent_category = await self.get_category(category_data.parent_id)
            if not parent_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent category not found"
                )
        
        # Create category
        category = Category(
            name=category_data.name,
            description=category_data.description,
            image_url=category_data.image_url,
            icon_url=category_data.icon_url,
            meta_title=category_data.meta_title,
            meta_description=category_data.meta_description,
            meta_keywords=category_data.meta_keywords,
            parent_id=category_data.parent_id,
            display_order=category_data.display_order,
            is_active=category_data.is_active,
            is_featured=category_data.is_featured,
            created_by=user_id
        )
        
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        
        # Cache category
        if self.cache:
            await self.cache.set_category(category)
            # Clear category tree cache
            await self.cache.delete("category_tree")
        
        return category
    
    async def get_category(self, category_id: str, increment_view: bool = False) -> Optional[Category]:
        """Get category by ID.
        
        Args:
            category_id: Category ID
            increment_view: Whether to increment view count
            
        Returns:
            Category object or None if not found
        """
        # Try cache first
        if self.cache:
            cached_category = await self.cache.get_category(category_id)
            if cached_category:
                if increment_view:
                    await self._increment_view_count(category_id)
                return cached_category
        
        # Query database
        result = await self.db.execute(
            select(Category)
            .options(
                selectinload(Category.children),
                selectinload(Category.parent)
            )
            .where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()
        
        if category:
            # Cache category
            if self.cache:
                await self.cache.set_category(category)
            
            # Increment view count
            if increment_view:
                await self._increment_view_count(category_id)
        
        return category
    
    async def get_category_by_slug(self, slug: str, increment_view: bool = False) -> Optional[Category]:
        """Get category by slug.
        
        Args:
            slug: Category slug
            increment_view: Whether to increment view count
            
        Returns:
            Category object or None if not found
        """
        result = await self.db.execute(
            select(Category)
            .options(
                selectinload(Category.children),
                selectinload(Category.parent)
            )
            .where(Category.slug == slug)
        )
        category = result.scalar_one_or_none()
        
        if category and increment_view:
            await self._increment_view_count(str(category.id))
        
        return category
    
    async def update_category(self, category_id: str, category_data: CategoryUpdate, user_id: str) -> Category:
        """Update an existing category.
        
        Args:
            category_id: Category ID
            category_data: Category update data
            user_id: ID of user updating the category
            
        Returns:
            Updated category object
            
        Raises:
            HTTPException: If category not found or circular reference detected
        """
        # Get existing category
        category = await self.get_category(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Validate parent category if being updated
        if category_data.parent_id is not None:
            if category_data.parent_id:
                # Check if parent exists
                parent_category = await self.get_category(category_data.parent_id)
                if not parent_category:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Parent category not found"
                    )
                
                # Check for circular reference
                if await self._would_create_circular_reference(category_id, category_data.parent_id):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot set parent: would create circular reference"
                    )
        
        # Update category fields
        update_data = category_data.dict(exclude_unset=True)
        update_data['updated_by'] = user_id
        
        for field, value in update_data.items():
            setattr(category, field, value)
        
        await self.db.commit()
        await self.db.refresh(category, ['children', 'parent'])
        
        # Clear cache
        if self.cache:
            await self.cache.delete_category(category_id)
            await self.cache.delete("category_tree")
        
        return category
    
    async def delete_category(self, category_id: str, force: bool = False) -> None:
        """Delete a category.
        
        Args:
            category_id: Category ID
            force: Whether to force delete even if category has children or products
            
        Raises:
            HTTPException: If category not found or has dependencies
        """
        category = await self.get_category(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Check for children
        if category.children and not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete category with children. Use force=true or move children first."
            )
        
        # Check for products
        if category.product_count > 0 and not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete category with products. Use force=true or move products first."
            )
        
        # If force delete, move children to parent
        if force and category.children:
            await self.db.execute(
                update(Category)
                .where(Category.parent_id == category_id)
                .values(parent_id=category.parent_id)
            )
        
        # Delete category
        await self.db.delete(category)
        await self.db.commit()
        
        # Clear cache
        if self.cache:
            await self.cache.delete_category(category_id)
            await self.cache.delete("category_tree")
    
    async def move_category(self, category_id: str, move_data: CategoryMove) -> Category:
        """Move category to different parent.
        
        Args:
            category_id: Category ID
            move_data: Move operation data
            
        Returns:
            Updated category object
            
        Raises:
            HTTPException: If category not found or circular reference detected
        """
        category = await self.get_category(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Validate new parent
        if move_data.new_parent_id:
            parent_category = await self.get_category(move_data.new_parent_id)
            if not parent_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New parent category not found"
                )
            
            # Check for circular reference
            if await self._would_create_circular_reference(category_id, move_data.new_parent_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot move category: would create circular reference"
                )
        
        # Update parent
        category.parent_id = move_data.new_parent_id
        
        # Update position if specified
        if move_data.new_position is not None:
            category.display_order = move_data.new_position
        
        await self.db.commit()
        await self.db.refresh(category, ['children', 'parent'])
        
        # Clear cache
        if self.cache:
            await self.cache.delete_category(category_id)
            await self.cache.delete("category_tree")
        
        return category
    
    async def get_categories(
        self,
        parent_id: Optional[str] = None,
        active_only: bool = True,
        featured_only: bool = False,
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResponse[Category] | List[Category]:
        """Get categories with optional filtering and pagination.
        
        Args:
            parent_id: Filter by parent category ID (None for root categories)
            active_only: Whether to return only active categories
            featured_only: Whether to return only featured categories
            pagination: Pagination parameters
            
        Returns:
            Paginated response or list of categories
        """
        # Build query
        query = select(Category).options(
            selectinload(Category.children),
            selectinload(Category.parent)
        )
        
        # Apply filters
        conditions = []
        
        if parent_id is not None:
            conditions.append(Category.parent_id == parent_id)
        else:
            conditions.append(Category.parent_id.is_(None))
        
        if active_only:
            conditions.append(Category.is_active == True)
        
        if featured_only:
            conditions.append(Category.is_featured == True)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Apply ordering
        query = query.order_by(Category.display_order, Category.name)
        
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
            categories = result.scalars().all()
            
            return PaginatedResponse(
                items=list(categories),
                total=total,
                page=pagination.page,
                size=pagination.size,
                pages=pagination.get_total_pages(total)
            )
        else:
            # Execute query without pagination
            result = await self.db.execute(query)
            return list(result.scalars().all())
    
    async def get_category_tree(self, active_only: bool = True) -> List[CategoryTree]:
        """Get complete category tree.
        
        Args:
            active_only: Whether to include only active categories
            
        Returns:
            List of root categories with nested children
        """
        # Try cache first
        cache_key = f"category_tree_{'active' if active_only else 'all'}"
        if self.cache:
            cached_tree = await self.cache.get(cache_key)
            if cached_tree:
                return cached_tree
        
        # Get all categories
        query = select(Category)
        if active_only:
            query = query.where(Category.is_active == True)
        
        query = query.order_by(Category.display_order, Category.name)
        result = await self.db.execute(query)
        all_categories = result.scalars().all()
        
        # Build tree structure
        category_dict = {str(cat.id): cat for cat in all_categories}
        tree = []
        
        for category in all_categories:
            if category.parent_id is None:
                # Root category
                tree_node = self._build_category_tree_node(category, category_dict)
                tree.append(tree_node)
        
        # Cache tree
        if self.cache:
            await self.cache.set(cache_key, tree, expire=3600)  # Cache for 1 hour
        
        return tree
    
    async def get_category_breadcrumbs(self, category_id: str) -> List[Category]:
        """Get breadcrumb trail for a category.
        
        Args:
            category_id: Category ID
            
        Returns:
            List of categories from root to current category
        """
        category = await self.get_category(category_id)
        if not category:
            return []
        
        breadcrumbs = []
        current = category
        
        while current:
            breadcrumbs.insert(0, current)
            if current.parent_id:
                current = await self.get_category(str(current.parent_id))
            else:
                current = None
        
        return breadcrumbs
    
    async def get_featured_categories(self, limit: int = 10) -> List[Category]:
        """Get featured categories.
        
        Args:
            limit: Maximum number of categories to return
            
        Returns:
            List of featured categories
        """
        # Try cache first
        if self.cache:
            cached_categories = await self.cache.get_featured_categories()
            if cached_categories:
                return cached_categories[:limit]
        
        # Query database
        result = await self.db.execute(
            select(Category)
            .options(
                selectinload(Category.children),
                selectinload(Category.parent)
            )
            .where(
                and_(
                    Category.is_featured == True,
                    Category.is_active == True
                )
            )
            .order_by(Category.display_order, desc(Category.product_count))
            .limit(limit)
        )
        categories = result.scalars().all()
        
        # Cache categories
        if self.cache and categories:
            await self.cache.set_featured_categories(list(categories))
        
        return list(categories)
    
    async def bulk_operation(self, operation_data: CategoryBulkOperation) -> Dict[str, int]:
        """Perform bulk operations on categories.
        
        Args:
            operation_data: Bulk operation data
            
        Returns:
            Dictionary with operation results
        """
        operation = operation_data.operation
        category_ids = operation_data.category_ids
        
        # Verify categories exist
        result = await self.db.execute(
            select(func.count()).where(Category.id.in_(category_ids))
        )
        existing_count = result.scalar()
        
        if existing_count != len(category_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some categories not found"
            )
        
        # Perform operation
        if operation == "activate":
            await self.db.execute(
                update(Category)
                .where(Category.id.in_(category_ids))
                .values(is_active=True)
            )
        elif operation == "deactivate":
            await self.db.execute(
                update(Category)
                .where(Category.id.in_(category_ids))
                .values(is_active=False)
            )
        elif operation == "feature":
            await self.db.execute(
                update(Category)
                .where(Category.id.in_(category_ids))
                .values(is_featured=True)
            )
        elif operation == "unfeature":
            await self.db.execute(
                update(Category)
                .where(Category.id.in_(category_ids))
                .values(is_featured=False)
            )
        elif operation == "delete":
            # Check for dependencies
            categories_with_children = await self.db.execute(
                select(func.count())
                .where(
                    and_(
                        Category.id.in_(category_ids),
                        Category.id.in_(
                            select(Category.parent_id).where(Category.parent_id.is_not(None))
                        )
                    )
                )
            )
            
            if categories_with_children.scalar() > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete categories that have children"
                )
            
            # Delete categories
            await self.db.execute(
                Category.__table__.delete().where(Category.id.in_(category_ids))
            )
        
        await self.db.commit()
        
        # Clear cache for affected categories
        if self.cache:
            for category_id in category_ids:
                await self.cache.delete_category(category_id)
            await self.cache.delete("category_tree")
        
        return {
            "operation": operation,
            "affected_count": len(category_ids),
            "success": True
        }
    
    async def get_category_stats(self, category_id: str) -> CategoryStats:
        """Get category statistics.
        
        Args:
            category_id: Category ID
            
        Returns:
            Category statistics
            
        Raises:
            HTTPException: If category not found
        """
        category = await self.get_category(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Get product statistics for this category
        from app.models.product import Product, ProductStatus
        
        # Count active products
        active_count_result = await self.db.execute(
            select(func.count())
            .select_from(Product)
            .join(Product.categories)
            .where(
                and_(
                    Category.id == category_id,
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
            .select_from(Product)
            .join(Product.categories)
            .where(
                and_(
                    Category.id == category_id,
                    Product.status == ProductStatus.ACTIVE
                )
            )
        )
        price_stats = price_stats_result.first()
        
        return CategoryStats(
            id=str(category.id),
            name=category.name,
            product_count=category.product_count,
            active_product_count=active_product_count,
            view_count=category.view_count,
            avg_product_price=price_stats[0],
            min_product_price=price_stats[1],
            max_product_price=price_stats[2],
            total_revenue=price_stats[3]
        )
    
    def _build_category_tree_node(self, category: Category, category_dict: Dict[str, Category]) -> CategoryTree:
        """Build a category tree node with children.
        
        Args:
            category: Category object
            category_dict: Dictionary of all categories by ID
            
        Returns:
            CategoryTree node with nested children
        """
        children = []
        
        # Find children of this category
        for cat_id, cat in category_dict.items():
            if cat.parent_id == category.id:
                child_node = self._build_category_tree_node(cat, category_dict)
                children.append(child_node)
        
        # Sort children by display order
        children.sort(key=lambda x: (x.display_order if hasattr(x, 'display_order') else 0, x.name))
        
        return CategoryTree(
            id=str(category.id),
            name=category.name,
            slug=category.slug,
            level=category.level,
            product_count=category.product_count,
            is_active=category.is_active,
            children=children
        )
    
    async def _would_create_circular_reference(self, category_id: str, new_parent_id: str) -> bool:
        """Check if setting new parent would create circular reference.
        
        Args:
            category_id: Category ID
            new_parent_id: Proposed new parent ID
            
        Returns:
            True if would create circular reference, False otherwise
        """
        # Check if new_parent_id is a descendant of category_id
        current_id = new_parent_id
        visited = set()
        
        while current_id and current_id not in visited:
            if current_id == category_id:
                return True
            
            visited.add(current_id)
            
            # Get parent of current category
            result = await self.db.execute(
                select(Category.parent_id).where(Category.id == current_id)
            )
            parent_result = result.scalar_one_or_none()
            current_id = str(parent_result) if parent_result else None
        
        return False
    
    async def _increment_view_count(self, category_id: str) -> None:
        """Increment category view count.
        
        Args:
            category_id: Category ID
        """
        await self.db.execute(
            update(Category)
            .where(Category.id == category_id)
            .values(view_count=Category.view_count + 1)
        )
        await self.db.commit()