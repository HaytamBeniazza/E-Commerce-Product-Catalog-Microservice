"""Category API endpoints.

This module provides endpoints for category management including
CRUD operations, hierarchy management, and category analytics.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    get_db_session,
    get_cache_service,
    get_current_active_user,
    get_admin_user,
    get_seller_user,
    get_pagination_params,
    get_search_params
)
from app.models.user import User as UserModel
from app.schemas.common import (
    SuccessResponse,
    PaginationParams,
    PaginatedResponse,
    SearchParams
)
from app.schemas.category import (
    Category,
    CategoryCreate,
    CategoryUpdate,
    CategoryMove,
    CategoryWithChildren,
    CategorySummary,
    CategoryBreadcrumb,
    CategoryTree,
    CategoryStats,
    CategoryBulkOperation
)
from app.services.cache_service import CacheService
from app.services.category_service import CategoryService

# Create router
router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post(
    "/",
    response_model=Category,
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
    description="Create a new category (Admin only)"
)
async def create_category(
    category_data: CategoryCreate,
    current_user: UserModel = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> Category:
    """Create a new category.
    
    Args:
        category_data: Category creation data
        current_user: Current authenticated admin user
        db: Database session
        cache: Cache service
        
    Returns:
        Created category
        
    Raises:
        HTTPException: If creation fails
    """
    category_service = CategoryService(db, cache)
    
    try:
        category = await category_service.create_category(
            category_data,
            str(current_user.id)
        )
        return category
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=PaginatedResponse[CategorySummary],
    summary="Get categories",
    description="Get categories with filtering, search, and pagination"
)
async def get_categories(
    search_params: SearchParams = Depends(get_search_params),
    pagination: PaginationParams = Depends(get_pagination_params),
    parent_id: Optional[str] = Query(None, description="Filter by parent category ID"),
    active_only: bool = Query(True, description="Show only active categories"),
    featured_only: bool = Query(False, description="Show only featured categories"),
    level: Optional[int] = Query(None, ge=0, le=10, description="Filter by hierarchy level"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> PaginatedResponse[CategorySummary]:
    """Get categories with filtering and pagination.
    
    Args:
        search_params: Search parameters
        pagination: Pagination parameters
        parent_id: Parent category filter
        active_only: Active status filter
        featured_only: Featured status filter
        level: Hierarchy level filter
        db: Database session
        cache: Cache service
        
    Returns:
        Paginated list of categories
    """
    category_service = CategoryService(db, cache)
    
    return await category_service.get_categories(
        parent_id=parent_id,
        active_only=active_only,
        featured_only=featured_only,
        level=level,
        search_query=search_params.query,
        pagination=pagination
    )


@router.get(
    "/tree",
    response_model=List[CategoryTree],
    summary="Get category tree",
    description="Get complete category hierarchy as a tree structure"
)
async def get_category_tree(
    active_only: bool = Query(True, description="Include only active categories"),
    max_depth: Optional[int] = Query(None, ge=1, le=10, description="Maximum tree depth"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> List[CategoryTree]:
    """Get category tree structure.
    
    Args:
        active_only: Include only active categories
        max_depth: Maximum tree depth
        db: Database session
        cache: Cache service
        
    Returns:
        Category tree structure
    """
    category_service = CategoryService(db, cache)
    
    return await category_service.get_category_tree(
        active_only=active_only,
        max_depth=max_depth
    )


@router.get(
    "/featured",
    response_model=List[CategorySummary],
    summary="Get featured categories",
    description="Get featured categories for homepage display"
)
async def get_featured_categories(
    limit: int = Query(10, ge=1, le=50, description="Number of categories to return"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> List[CategorySummary]:
    """Get featured categories.
    
    Args:
        limit: Maximum number of categories to return
        db: Database session
        cache: Cache service
        
    Returns:
        List of featured categories
    """
    category_service = CategoryService(db, cache)
    return await category_service.get_featured_categories(limit)


@router.get(
    "/{category_id}",
    response_model=CategoryWithChildren,
    summary="Get category by ID",
    description="Get detailed category information with children"
)
async def get_category(
    category_id: str,
    include_children: bool = Query(True, description="Include child categories"),
    increment_view: bool = Query(True, description="Increment view count"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> CategoryWithChildren:
    """Get category by ID.
    
    Args:
        category_id: Category ID
        include_children: Whether to include child categories
        increment_view: Whether to increment view count
        db: Database session
        cache: Cache service
        
    Returns:
        Category details with children
        
    Raises:
        HTTPException: If category not found
    """
    category_service = CategoryService(db, cache)
    
    category = await category_service.get_category(
        category_id,
        increment_view=increment_view
    )
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Convert to CategoryWithChildren if needed
    if include_children:
        children = await category_service.get_categories(
            parent_id=category_id,
            active_only=True
        )
        
        return CategoryWithChildren(
            **category.dict(),
            children=children.items if hasattr(children, 'items') else children
        )
    else:
        return CategoryWithChildren(
            **category.dict(),
            children=[]
        )


@router.get(
    "/slug/{slug}",
    response_model=CategoryWithChildren,
    summary="Get category by slug",
    description="Get detailed category information by slug"
)
async def get_category_by_slug(
    slug: str,
    include_children: bool = Query(True, description="Include child categories"),
    increment_view: bool = Query(True, description="Increment view count"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> CategoryWithChildren:
    """Get category by slug.
    
    Args:
        slug: Category slug
        include_children: Whether to include child categories
        increment_view: Whether to increment view count
        db: Database session
        cache: Cache service
        
    Returns:
        Category details with children
        
    Raises:
        HTTPException: If category not found
    """
    category_service = CategoryService(db, cache)
    
    category = await category_service.get_category_by_slug(
        slug,
        increment_view=increment_view
    )
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Convert to CategoryWithChildren if needed
    if include_children:
        children = await category_service.get_categories(
            parent_id=str(category.id),
            active_only=True
        )
        
        return CategoryWithChildren(
            **category.dict(),
            children=children.items if hasattr(children, 'items') else children
        )
    else:
        return CategoryWithChildren(
            **category.dict(),
            children=[]
        )


@router.get(
    "/{category_id}/breadcrumbs",
    response_model=List[CategoryBreadcrumb],
    summary="Get category breadcrumbs",
    description="Get breadcrumb navigation for category"
)
async def get_category_breadcrumbs(
    category_id: str,
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> List[CategoryBreadcrumb]:
    """Get category breadcrumbs.
    
    Args:
        category_id: Category ID
        db: Database session
        cache: Cache service
        
    Returns:
        List of breadcrumb items
        
    Raises:
        HTTPException: If category not found
    """
    category_service = CategoryService(db, cache)
    
    try:
        breadcrumbs = await category_service.get_category_breadcrumbs(category_id)
        return breadcrumbs
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put(
    "/{category_id}",
    response_model=Category,
    summary="Update category",
    description="Update category information (Admin only)"
)
async def update_category(
    category_id: str,
    category_data: CategoryUpdate,
    current_user: UserModel = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> Category:
    """Update category.
    
    Args:
        category_id: Category ID
        category_data: Category update data
        current_user: Current authenticated admin user
        db: Database session
        cache: Cache service
        
    Returns:
        Updated category
        
    Raises:
        HTTPException: If update fails
    """
    category_service = CategoryService(db, cache)
    
    try:
        category = await category_service.update_category(
            category_id,
            category_data,
            str(current_user.id)
        )
        return category
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{category_id}/move",
    response_model=Category,
    summary="Move category",
    description="Move category to different parent (Admin only)"
)
async def move_category(
    category_id: str,
    move_data: CategoryMove,
    current_user: UserModel = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> Category:
    """Move category to different parent.
    
    Args:
        category_id: Category ID to move
        move_data: Move operation data
        current_user: Current authenticated admin user
        db: Database session
        cache: Cache service
        
    Returns:
        Updated category
        
    Raises:
        HTTPException: If move operation fails
    """
    category_service = CategoryService(db, cache)
    
    try:
        category = await category_service.move_category(
            category_id,
            move_data.new_parent_id,
            move_data.new_display_order
        )
        return category
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{category_id}",
    response_model=SuccessResponse,
    summary="Delete category",
    description="Delete category (Admin only)"
)
async def delete_category(
    category_id: str,
    force: bool = Query(False, description="Force delete even if category has products or children"),
    current_user: UserModel = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> SuccessResponse:
    """Delete category.
    
    Args:
        category_id: Category ID
        force: Whether to force delete
        current_user: Current authenticated admin user
        db: Database session
        cache: Cache service
        
    Returns:
        Success response
        
    Raises:
        HTTPException: If deletion fails
    """
    category_service = CategoryService(db, cache)
    
    try:
        await category_service.delete_category(category_id, force=force)
        
        return SuccessResponse(
            message="Category deleted successfully",
            data={"category_id": category_id}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/bulk",
    response_model=SuccessResponse,
    summary="Bulk category operations",
    description="Perform bulk operations on categories (Admin only)"
)
async def bulk_category_operations(
    operation_data: CategoryBulkOperation,
    current_user: UserModel = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> SuccessResponse:
    """Perform bulk operations on categories.
    
    Args:
        operation_data: Bulk operation data
        current_user: Current authenticated admin user
        db: Database session
        cache: Cache service
        
    Returns:
        Success response with operation results
        
    Raises:
        HTTPException: If operation fails
    """
    category_service = CategoryService(db, cache)
    
    try:
        result = await category_service.bulk_operation(operation_data)
        
        return SuccessResponse(
            message=f"Bulk {operation_data.operation} completed successfully",
            data=result
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{category_id}/stats",
    response_model=CategoryStats,
    summary="Get category statistics",
    description="Get detailed category analytics and statistics"
)
async def get_category_stats(
    category_id: str,
    include_children: bool = Query(True, description="Include statistics from child categories"),
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> CategoryStats:
    """Get category statistics.
    
    Args:
        category_id: Category ID
        include_children: Whether to include child category stats
        current_user: Current authenticated user
        db: Database session
        cache: Cache service
        
    Returns:
        Category statistics
        
    Raises:
        HTTPException: If category not found
    """
    category_service = CategoryService(db, cache)
    
    try:
        stats = await category_service.get_category_stats(
            category_id,
            include_children=include_children
        )
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/{category_id}/children",
    response_model=List[CategorySummary],
    summary="Get category children",
    description="Get direct child categories"
)
async def get_category_children(
    category_id: str,
    active_only: bool = Query(True, description="Show only active categories"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> List[CategorySummary]:
    """Get category children.
    
    Args:
        category_id: Parent category ID
        active_only: Show only active categories
        db: Database session
        cache: Cache service
        
    Returns:
        List of child categories
        
    Raises:
        HTTPException: If parent category not found
    """
    category_service = CategoryService(db, cache)
    
    # Verify parent category exists
    parent_category = await category_service.get_category(category_id)
    if not parent_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent category not found"
        )
    
    children = await category_service.get_categories(
        parent_id=category_id,
        active_only=active_only
    )
    
    return children.items if hasattr(children, 'items') else children


@router.get(
    "/{category_id}/products/count",
    response_model=dict,
    summary="Get category product count",
    description="Get number of products in category and its children"
)
async def get_category_product_count(
    category_id: str,
    include_children: bool = Query(True, description="Include products from child categories"),
    active_only: bool = Query(True, description="Count only active products"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> dict:
    """Get category product count.
    
    Args:
        category_id: Category ID
        include_children: Include child category products
        active_only: Count only active products
        db: Database session
        cache: Cache service
        
    Returns:
        Product count information
        
    Raises:
        HTTPException: If category not found
    """
    category_service = CategoryService(db, cache)
    
    # Verify category exists
    category = await category_service.get_category(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Get product count from category stats
    stats = await category_service.get_category_stats(
        category_id,
        include_children=include_children
    )
    
    return {
        "category_id": category_id,
        "category_name": category.name,
        "direct_product_count": category.product_count,
        "total_product_count": stats.total_product_count if include_children else category.product_count,
        "include_children": include_children,
        "active_only": active_only
    }
