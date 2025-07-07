"""Product API endpoints.

This module provides endpoints for product management including
CRUD operations, search, filtering, inventory management, and analytics.
"""

from typing import List, Optional
from uuid import UUID

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
from app.schemas.product import (
    Product,
    ProductCreate,
    ProductUpdate,
    ProductSummary,
    ProductStats,
    ProductBulkOperation,
    ProductSearch,
    ProductImage,
    ProductImageCreate,
    ProductImageUpdate
)
from app.services.cache_service import CacheService
from app.services.product_service import ProductService

# Create router
router = APIRouter(prefix="/products", tags=["Products"])


@router.post(
    "/",
    response_model=Product,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
    description="Create a new product (Admin/Seller only)"
)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_seller_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> Product:
    """Create a new product.
    
    Args:
        product_data: Product creation data
        current_user: Current authenticated user (seller/admin)
        db: Database session
        cache: Cache service
        
    Returns:
        Created product
        
    Raises:
        HTTPException: If creation fails
    """
    product_service = ProductService(db, cache)
    
    try:
        product = await product_service.create_product(
            product_data,
            str(current_user.id)
        )
        return product
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=PaginatedResponse[ProductSummary],
    summary="Get products",
    description="Get products with filtering, search, and pagination"
)
async def get_products(
    search_params: SearchParams = Depends(get_search_params),
    pagination: PaginationParams = Depends(get_pagination_params),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    brand_id: Optional[str] = Query(None, description="Filter by brand ID"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    in_stock_only: bool = Query(True, description="Show only products in stock"),
    active_only: bool = Query(True, description="Show only active products"),
    featured_only: bool = Query(False, description="Show only featured products"),
    on_sale_only: bool = Query(False, description="Show only products on sale"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> PaginatedResponse[ProductSummary]:
    """Get products with filtering and pagination.
    
    Args:
        search_params: Search parameters
        pagination: Pagination parameters
        category_id: Category filter
        brand_id: Brand filter
        min_price: Minimum price filter
        max_price: Maximum price filter
        in_stock_only: Stock filter
        active_only: Active status filter
        featured_only: Featured status filter
        on_sale_only: Sale status filter
        db: Database session
        cache: Cache service
        
    Returns:
        Paginated list of products
    """
    product_service = ProductService(db, cache)
    
    # Build search criteria
    search_criteria = ProductSearch(
        query=search_params.query,
        category_id=category_id,
        brand_id=brand_id,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        active_only=active_only,
        featured_only=featured_only,
        on_sale_only=on_sale_only,
        sort_by=search_params.sort_by,
        sort_order=search_params.sort_order
    )
    
    return await product_service.search_products(
        search_criteria,
        pagination
    )


@router.get(
    "/featured",
    response_model=List[ProductSummary],
    summary="Get featured products",
    description="Get featured products for homepage display"
)
async def get_featured_products(
    limit: int = Query(10, ge=1, le=50, description="Number of products to return"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> List[ProductSummary]:
    """Get featured products.
    
    Args:
        limit: Maximum number of products to return
        db: Database session
        cache: Cache service
        
    Returns:
        List of featured products
    """
    product_service = ProductService(db, cache)
    return await product_service.get_featured_products(limit)


@router.get(
    "/search",
    response_model=PaginatedResponse[ProductSummary],
    summary="Search products",
    description="Advanced product search with full-text search capabilities"
)
async def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    pagination: PaginationParams = Depends(get_pagination_params),
    category_id: Optional[str] = Query(None, description="Filter by category"),
    brand_id: Optional[str] = Query(None, description="Filter by brand"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    sort_by: str = Query("relevance", description="Sort by: relevance, price, rating, created_at"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> PaginatedResponse[ProductSummary]:
    """Search products with advanced filtering.
    
    Args:
        q: Search query
        pagination: Pagination parameters
        category_id: Category filter
        brand_id: Brand filter
        min_price: Minimum price filter
        max_price: Maximum price filter
        sort_by: Sort field
        sort_order: Sort direction
        db: Database session
        cache: Cache service
        
    Returns:
        Paginated search results
    """
    product_service = ProductService(db, cache)
    
    search_criteria = ProductSearch(
        query=q,
        category_id=category_id,
        brand_id=brand_id,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return await product_service.search_products(
        search_criteria,
        pagination
    )


@router.get(
    "/{product_id}",
    response_model=Product,
    summary="Get product by ID",
    description="Get detailed product information by ID"
)
async def get_product(
    product_id: str,
    increment_view: bool = Query(True, description="Increment view count"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> Product:
    """Get product by ID.
    
    Args:
        product_id: Product ID
        increment_view: Whether to increment view count
        db: Database session
        cache: Cache service
        
    Returns:
        Product details
        
    Raises:
        HTTPException: If product not found
    """
    product_service = ProductService(db, cache)
    
    product = await product_service.get_product(
        product_id,
        increment_view=increment_view
    )
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@router.get(
    "/slug/{slug}",
    response_model=Product,
    summary="Get product by slug",
    description="Get detailed product information by slug"
)
async def get_product_by_slug(
    slug: str,
    increment_view: bool = Query(True, description="Increment view count"),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> Product:
    """Get product by slug.
    
    Args:
        slug: Product slug
        increment_view: Whether to increment view count
        db: Database session
        cache: Cache service
        
    Returns:
        Product details
        
    Raises:
        HTTPException: If product not found
    """
    product_service = ProductService(db, cache)
    
    product = await product_service.get_product_by_slug(
        slug,
        increment_view=increment_view
    )
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@router.put(
    "/{product_id}",
    response_model=Product,
    summary="Update product",
    description="Update product information (Admin/Seller only)"
)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    current_user: User = Depends(get_seller_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> Product:
    """Update product.
    
    Args:
        product_id: Product ID
        product_data: Product update data
        current_user: Current authenticated user (seller/admin)
        db: Database session
        cache: Cache service
        
    Returns:
        Updated product
        
    Raises:
        HTTPException: If update fails or unauthorized
    """
    product_service = ProductService(db, cache)
    
    try:
        product = await product_service.update_product(
            product_id,
            product_data,
            str(current_user.id)
        )
        return product
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.delete(
    "/{product_id}",
    response_model=SuccessResponse,
    summary="Delete product",
    description="Delete product (Admin/Seller only)"
)
async def delete_product(
    product_id: str,
    current_user: User = Depends(get_seller_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> SuccessResponse:
    """Delete product.
    
    Args:
        product_id: Product ID
        current_user: Current authenticated user (seller/admin)
        db: Database session
        cache: Cache service
        
    Returns:
        Success response
        
    Raises:
        HTTPException: If deletion fails or unauthorized
    """
    product_service = ProductService(db, cache)
    
    try:
        await product_service.delete_product(
            product_id,
            str(current_user.id)
        )
        
        return SuccessResponse(
            message="Product deleted successfully",
            data={"product_id": product_id}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post(
    "/bulk",
    response_model=SuccessResponse,
    summary="Bulk product operations",
    description="Perform bulk operations on products (Admin only)"
)
async def bulk_product_operations(
    operation_data: ProductBulkOperation,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> SuccessResponse:
    """Perform bulk operations on products.
    
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
    product_service = ProductService(db, cache)
    
    try:
        result = await product_service.bulk_operation(operation_data)
        
        return SuccessResponse(
            message=f"Bulk {operation_data.operation} completed successfully",
            data=result
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{product_id}/stock",
    response_model=SuccessResponse,
    summary="Update product stock",
    description="Update product stock quantity (Admin/Seller only)"
)
async def update_product_stock(
    product_id: str,
    quantity: int = Query(..., description="New stock quantity"),
    operation: str = Query("set", description="Operation: set, add, subtract"),
    current_user: User = Depends(get_seller_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> SuccessResponse:
    """Update product stock.
    
    Args:
        product_id: Product ID
        quantity: Quantity to set/add/subtract
        operation: Stock operation type
        current_user: Current authenticated user (seller/admin)
        db: Database session
        cache: Cache service
        
    Returns:
        Success response with new stock level
        
    Raises:
        HTTPException: If operation fails
    """
    product_service = ProductService(db, cache)
    
    try:
        new_stock = await product_service.update_stock(
            product_id,
            quantity,
            operation
        )
        
        return SuccessResponse(
            message="Stock updated successfully",
            data={
                "product_id": product_id,
                "new_stock": new_stock,
                "operation": operation,
                "quantity": quantity
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{product_id}/stats",
    response_model=ProductStats,
    summary="Get product statistics",
    description="Get detailed product analytics and statistics"
)
async def get_product_stats(
    product_id: str,
    current_user: User = Depends(get_seller_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> ProductStats:
    """Get product statistics.
    
    Args:
        product_id: Product ID
        current_user: Current authenticated user (seller/admin)
        db: Database session
        cache: Cache service
        
    Returns:
        Product statistics
        
    Raises:
        HTTPException: If product not found
    """
    product_service = ProductService(db, cache)
    
    try:
        stats = await product_service.get_product_stats(product_id)
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# Product Images endpoints
@router.post(
    "/{product_id}/images",
    response_model=ProductImage,
    status_code=status.HTTP_201_CREATED,
    summary="Add product image",
    description="Add image to product (Admin/Seller only)"
)
async def add_product_image(
    product_id: str,
    image_data: ProductImageCreate,
    current_user: User = Depends(get_seller_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> ProductImage:
    """Add image to product.
    
    Args:
        product_id: Product ID
        image_data: Image data
        current_user: Current authenticated user (seller/admin)
        db: Database session
        cache: Cache service
        
    Returns:
        Created product image
        
    Raises:
        HTTPException: If operation fails
    """
    product_service = ProductService(db, cache)
    
    try:
        image = await product_service.add_product_image(
            product_id,
            image_data
        )
        return image
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{product_id}/images/{image_id}",
    response_model=ProductImage,
    summary="Update product image",
    description="Update product image information (Admin/Seller only)"
)
async def update_product_image(
    product_id: str,
    image_id: str,
    image_data: ProductImageUpdate,
    current_user: User = Depends(get_seller_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> ProductImage:
    """Update product image.
    
    Args:
        product_id: Product ID
        image_id: Image ID
        image_data: Image update data
        current_user: Current authenticated user (seller/admin)
        db: Database session
        cache: Cache service
        
    Returns:
        Updated product image
        
    Raises:
        HTTPException: If operation fails
    """
    product_service = ProductService(db, cache)
    
    try:
        image = await product_service.update_product_image(
            product_id,
            image_id,
            image_data
        )
        return image
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{product_id}/images/{image_id}",
    response_model=SuccessResponse,
    summary="Delete product image",
    description="Delete product image (Admin/Seller only)"
)
async def delete_product_image(
    product_id: str,
    image_id: str,
    current_user: User = Depends(get_seller_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> SuccessResponse:
    """Delete product image.
    
    Args:
        product_id: Product ID
        image_id: Image ID
        current_user: Current authenticated user (seller/admin)
        db: Database session
        cache: Cache service
        
    Returns:
        Success response
        
    Raises:
        HTTPException: If operation fails
    """
    product_service = ProductService(db, cache)
    
    try:
        await product_service.delete_product_image(
            product_id,
            image_id
        )
        
        return SuccessResponse(
            message="Product image deleted successfully",
            data={
                "product_id": product_id,
                "image_id": image_id
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )