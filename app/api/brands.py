"""Brand API endpoints.

This module provides endpoints for brand management including
CRUD operations, brand analytics, and brand comparison features.
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
from app.models.user import User
from app.schemas.common import (
    SuccessResponse,
    PaginationParams,
    PaginatedResponse,
    SearchParams
)
from app.schemas.brand import (
    Brand,
    BrandCreate,
    BrandUpdate,
    BrandSummary,
    BrandStats,
    BrandBulkOperation,
    BrandComparison
)
from app.services.cache_service import CacheService
from app.services.brand_service import BrandService

# Create router
router = APIRouter(prefix="/brands", tags=["Brands"])


@router.post(
    "/",
    response_model=Brand,
    status_code=status.HTTP_201_CREATED,
    summary="Create brand",
    description="Create a new brand (Admin/Seller only)"
)
async def create_brand(
    brand_data: BrandCreate,
    current_user: User = Depends(get_seller_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> Brand:
    """Create a new brand.
    
    Args:
        brand_data: Brand creation data
        current_user: Current authenticated user (seller/admin)
        db: Database session
        cache: Cache service
        
    Returns:
        Created brand
        
    Raises:
        HTTPException: If creation fails
    """
    brand_service = BrandService(db, cache)
    
    try:
        brand = await brand_service.create_brand(
            brand_data,
            str(current_user.id)
        )
        return brand
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=PaginatedResponse[BrandSummary],
    summary="Get brands",
    description="Get brands with filtering, search, and pagination"
)
async def get_brands(
    search_params: SearchParams = Depends(get_search_params),
    pagination: PaginationParams = Depends(get_pagination_params),
    active_only: bool = Query(True, description="Show only active brands"),
    featured_only: bool = Query(False, description="Show only featured brands"),
    verified_only: bool = Query(False, description="Show only verified brands"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> PaginatedResponse[BrandSummary]:
    """Get brands with filtering and pagination.
    
    Args:
        search_params: Search parameters
        pagination: Pagination parameters
        active_only: Active status filter
        featured_only: Featured status filter
        verified_only: Verified status filter
        db: Database session
        cache: Cache service
        
    Returns:
        Paginated list of brands
    """
    brand_service = BrandService(db, cache)
    
    return await brand_service.get_brands(
        active_only=active_only,
        featured_only=featured_only,
        verified_only=verified_only,
        search_query=search_params.query,
        pagination=pagination
    )


@router.get(
    "/featured",
    response_model=List[BrandSummary],
    summary="Get featured brands",
    description="Get featured brands for homepage display"
)
async def get_featured_brands(
    limit: int = Query(10, ge=1, le=50, description="Number of brands to return"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> List[BrandSummary]:
    """Get featured brands.
    
    Args:
        limit: Maximum number of brands to return
        db: Database session
        cache: Cache service
        
    Returns:
        List of featured brands
    """
    brand_service = BrandService(db, cache)
    brands = await brand_service.get_featured_brands(limit)
    
    # Convert to BrandSummary
    return [BrandSummary.from_orm(brand) for brand in brands]


@router.get(
    "/top",
    response_model=List[BrandSummary],
    summary="Get top brands",
    description="Get top brands by specified metric"
)
async def get_top_brands(
    metric: str = Query("product_count", description="Metric: product_count, rating, view_count, review_count"),
    limit: int = Query(10, ge=1, le=50, description="Number of brands to return"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> List[BrandSummary]:
    """Get top brands by metric.
    
    Args:
        metric: Metric to sort by
        limit: Maximum number of brands to return
        db: Database session
        cache: Cache service
        
    Returns:
        List of top brands
        
    Raises:
        HTTPException: If invalid metric
    """
    brand_service = BrandService(db, cache)
    
    try:
        brands = await brand_service.get_top_brands(limit, metric)
        return [BrandSummary.from_orm(brand) for brand in brands]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{brand_id}",
    response_model=Brand,
    summary="Get brand by ID",
    description="Get detailed brand information by ID"
)
async def get_brand(
    brand_id: str,
    increment_view: bool = Query(True, description="Increment view count"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> Brand:
    """Get brand by ID.
    
    Args:
        brand_id: Brand ID
        increment_view: Whether to increment view count
        db: Database session
        cache: Cache service
        
    Returns:
        Brand details
        
    Raises:
        HTTPException: If brand not found
    """
    brand_service = BrandService(db, cache)
    
    brand = await brand_service.get_brand(
        brand_id,
        increment_view=increment_view
    )
    
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    
    return brand


@router.get(
    "/slug/{slug}",
    response_model=Brand,
    summary="Get brand by slug",
    description="Get detailed brand information by slug"
)
async def get_brand_by_slug(
    slug: str,
    increment_view: bool = Query(True, description="Increment view count"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> Brand:
    """Get brand by slug.
    
    Args:
        slug: Brand slug
        increment_view: Whether to increment view count
        db: Database session
        cache: Cache service
        
    Returns:
        Brand details
        
    Raises:
        HTTPException: If brand not found
    """
    brand_service = BrandService(db, cache)
    
    brand = await brand_service.get_brand_by_slug(
        slug,
        increment_view=increment_view
    )
    
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    
    return brand


@router.put(
    "/{brand_id}",
    response_model=Brand,
    summary="Update brand",
    description="Update brand information (Admin/Seller only)"
)
async def update_brand(
    brand_id: str,
    brand_data: BrandUpdate,
    current_user: User = Depends(get_seller_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> Brand:
    """Update brand.
    
    Args:
        brand_id: Brand ID
        brand_data: Brand update data
        current_user: Current authenticated user (seller/admin)
        db: Database session
        cache: Cache service
        
    Returns:
        Updated brand
        
    Raises:
        HTTPException: If update fails
    """
    brand_service = BrandService(db, cache)
    
    try:
        brand = await brand_service.update_brand(
            brand_id,
            brand_data,
            str(current_user.id)
        )
        return brand
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{brand_id}",
    response_model=SuccessResponse,
    summary="Delete brand",
    description="Delete brand (Admin only)"
)
async def delete_brand(
    brand_id: str,
    force: bool = Query(False, description="Force delete even if brand has products"),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> SuccessResponse:
    """Delete brand.
    
    Args:
        brand_id: Brand ID
        force: Whether to force delete
        current_user: Current authenticated admin user
        db: Database session
        cache: Cache service
        
    Returns:
        Success response
        
    Raises:
        HTTPException: If deletion fails
    """
    brand_service = BrandService(db, cache)
    
    try:
        await brand_service.delete_brand(brand_id, force=force)
        
        return SuccessResponse(
            message="Brand deleted successfully",
            data={"brand_id": brand_id}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/bulk",
    response_model=SuccessResponse,
    summary="Bulk brand operations",
    description="Perform bulk operations on brands (Admin only)"
)
async def bulk_brand_operations(
    operation_data: BrandBulkOperation,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> SuccessResponse:
    """Perform bulk operations on brands.
    
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
    brand_service = BrandService(db, cache)
    
    try:
        result = await brand_service.bulk_operation(operation_data)
        
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
    "/{brand_id}/stats",
    response_model=BrandStats,
    summary="Get brand statistics",
    description="Get detailed brand analytics and statistics"
)
async def get_brand_stats(
    brand_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> BrandStats:
    """Get brand statistics.
    
    Args:
        brand_id: Brand ID
        current_user: Current authenticated user
        db: Database session
        cache: Cache service
        
    Returns:
        Brand statistics
        
    Raises:
        HTTPException: If brand not found
    """
    brand_service = BrandService(db, cache)
    
    try:
        stats = await brand_service.get_brand_stats(brand_id)
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/compare",
    response_model=BrandComparison,
    summary="Compare brands",
    description="Compare multiple brands side by side"
)
async def compare_brands(
    brand_ids: List[str] = Query(..., min_items=2, max_items=5, description="Brand IDs to compare"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> BrandComparison:
    """Compare multiple brands.
    
    Args:
        brand_ids: List of brand IDs to compare
        current_user: Current authenticated user
        db: Database session
        cache: Cache service
        
    Returns:
        Brand comparison data
        
    Raises:
        HTTPException: If comparison fails
    """
    brand_service = BrandService(db, cache)
    
    try:
        comparison = await brand_service.compare_brands(brand_ids)
        return comparison
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{brand_id}/rating",
    response_model=SuccessResponse,
    summary="Update brand rating",
    description="Update brand rating (Internal use - typically called by review service)"
)
async def update_brand_rating(
    brand_id: str,
    rating: float = Query(..., ge=0, le=5, description="New rating value"),
    review_count_delta: int = Query(1, description="Change in review count"),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> SuccessResponse:
    """Update brand rating.
    
    Args:
        brand_id: Brand ID
        rating: New rating to incorporate
        review_count_delta: Change in review count
        current_user: Current authenticated admin user
        db: Database session
        cache: Cache service
        
    Returns:
        Success response
        
    Raises:
        HTTPException: If brand not found
    """
    brand_service = BrandService(db, cache)
    
    try:
        await brand_service.update_brand_rating(
            brand_id,
            rating,
            review_count_delta
        )
        
        return SuccessResponse(
            message="Brand rating updated successfully",
            data={
                "brand_id": brand_id,
                "rating": rating,
                "review_count_delta": review_count_delta
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update brand rating"
        )


@router.get(
    "/{brand_id}/products/count",
    response_model=dict,
    summary="Get brand product count",
    description="Get number of products for this brand"
)
async def get_brand_product_count(
    brand_id: str,
    active_only: bool = Query(True, description="Count only active products"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> dict:
    """Get brand product count.
    
    Args:
        brand_id: Brand ID
        active_only: Count only active products
        db: Database session
        cache: Cache service
        
    Returns:
        Product count information
        
    Raises:
        HTTPException: If brand not found
    """
    brand_service = BrandService(db, cache)
    
    # Verify brand exists
    brand = await brand_service.get_brand(brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    
    # Get product count from brand stats
    stats = await brand_service.get_brand_stats(brand_id)
    
    return {
        "brand_id": brand_id,
        "brand_name": brand.name,
        "total_product_count": brand.product_count,
        "active_product_count": stats.active_product_count,
        "active_only": active_only
    }


@router.get(
    "/{brand_id}/products",
    response_model=PaginatedResponse,
    summary="Get brand products",
    description="Get products for this brand"
)
async def get_brand_products(
    brand_id: str,
    pagination: PaginationParams = Depends(get_pagination_params),
    active_only: bool = Query(True, description="Show only active products"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> PaginatedResponse:
    """Get products for brand.
    
    Args:
        brand_id: Brand ID
        pagination: Pagination parameters
        active_only: Show only active products
        db: Database session
        cache: Cache service
        
    Returns:
        Paginated list of products
        
    Raises:
        HTTPException: If brand not found
    """
    brand_service = BrandService(db, cache)
    
    # Verify brand exists
    brand = await brand_service.get_brand(brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    
    # Import here to avoid circular imports
    from app.services.product_service import ProductService
    from app.schemas.product import ProductSearch
    
    product_service = ProductService(db, cache)
    
    # Create search criteria for this brand
    search_criteria = ProductSearch(
        brand_id=brand_id,
        active_only=active_only
    )
    
    return await product_service.search_products(
        search_criteria,
        pagination
    )