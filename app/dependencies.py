"""FastAPI dependency injection module.

This module provides dependency injection functions for FastAPI endpoints,
including database sessions, cache services, authentication, and other
commonly used dependencies.
"""

import logging
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database.connection import get_db_session
from app.services.cache_service import CacheService, get_cache_service

logger = logging.getLogger(__name__)

# Security scheme for JWT authentication
security = HTTPBearer(auto_error=False)


# Database dependency
async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency.
    
    Yields:
        AsyncSession: Database session
    """
    async for session in get_db_session():
        yield session


# Cache dependency
async def get_cache() -> CacheService:
    """Get cache service dependency.
    
    Returns:
        CacheService: Cache service instance
    """
    return await get_cache_service()


# Configuration dependency
def get_config() -> Settings:
    """Get application settings dependency.
    
    Returns:
        Settings: Application configuration
    """
    return get_settings()


# Authentication dependencies
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    cache: CacheService = Depends(get_cache)
) -> Optional[dict]:
    """Get current user from JWT token (optional).
    
    This dependency extracts user information from JWT token if provided,
    but doesn't raise an error if no token is present.
    
    Args:
        credentials: HTTP authorization credentials
        cache: Cache service for session management
        
    Returns:
        User data if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        # Import here to avoid circular imports
        from app.services.auth_service import AuthService
        
        auth_service = AuthService(cache)
        user = await auth_service.get_current_user(credentials.credentials)
        return user
        
    except Exception as e:
        logger.warning(f"Optional authentication failed: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    cache: CacheService = Depends(get_cache)
) -> dict:
    """Get current user from JWT token (required).
    
    This dependency extracts user information from JWT token and raises
    an HTTP 401 error if authentication fails.
    
    Args:
        credentials: HTTP authorization credentials
        cache: Cache service for session management
        
    Returns:
        User data
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Import here to avoid circular imports
        from app.services.auth_service import AuthService
        
        auth_service = AuthService(cache)
        user = await auth_service.get_current_user(credentials.credentials)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_admin_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get current admin user.
    
    This dependency ensures the current user has admin privileges.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Admin user data
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.get("is_admin") and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


async def get_current_seller_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get current seller user.
    
    This dependency ensures the current user has seller privileges or higher.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Seller user data
        
    Raises:
        HTTPException: If user is not a seller or admin
    """
    user_role = current_user.get("role", "buyer")
    if user_role not in ["seller", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller privileges required"
        )
    
    return current_user


# Pagination dependencies
class PaginationParams:
    """Pagination parameters for list endpoints."""
    
    def __init__(
        self,
        page: int = 1,
        size: int = 20,
        settings: Settings = Depends(get_config)
    ):
        """Initialize pagination parameters.
        
        Args:
            page: Page number (1-based)
            size: Page size
            settings: Application settings
        """
        self.page = max(1, page)
        self.size = min(max(1, size), settings.MAX_PAGE_SIZE)
        self.offset = (self.page - 1) * self.size
        self.limit = self.size


def get_pagination_params(
    page: int = 1,
    size: int = 20,
    settings: Settings = Depends(get_config)
) -> PaginationParams:
    """Get pagination parameters dependency.
    
    Args:
        page: Page number (1-based)
        size: Page size
        settings: Application settings
        
    Returns:
        PaginationParams: Pagination parameters
    """
    return PaginationParams(page, size, settings)


# Search and filtering dependencies
class SearchParams:
    """Search parameters for product search endpoints."""
    
    def __init__(
        self,
        q: Optional[str] = None,
        category_id: Optional[str] = None,
        brand_id: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        """Initialize search parameters.
        
        Args:
            q: Search query
            category_id: Category filter
            brand_id: Brand filter
            min_price: Minimum price filter
            max_price: Maximum price filter
            in_stock: Stock availability filter
            sort_by: Sort field
            sort_order: Sort order (asc/desc)
        """
        self.query = q
        self.category_id = category_id
        self.brand_id = brand_id
        self.min_price = min_price
        self.max_price = max_price
        self.in_stock = in_stock
        self.sort_by = sort_by
        self.sort_order = sort_order.lower() if sort_order else "desc"
        
        # Validate sort order
        if self.sort_order not in ["asc", "desc"]:
            self.sort_order = "desc"
        
        # Validate sort field
        valid_sort_fields = [
            "created_at", "updated_at", "name", "price", 
            "rating", "review_count", "stock_quantity"
        ]
        if self.sort_by not in valid_sort_fields:
            self.sort_by = "created_at"


def get_search_params(
    q: Optional[str] = None,
    category_id: Optional[str] = None,
    brand_id: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> SearchParams:
    """Get search parameters dependency.
    
    Args:
        q: Search query
        category_id: Category filter
        brand_id: Brand filter
        min_price: Minimum price filter
        max_price: Maximum price filter
        in_stock: Stock availability filter
        sort_by: Sort field
        sort_order: Sort order (asc/desc)
        
    Returns:
        SearchParams: Search parameters
    """
    return SearchParams(
        q=q,
        category_id=category_id,
        brand_id=brand_id,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        sort_by=sort_by,
        sort_order=sort_order
    )


# Rate limiting dependency
async def rate_limit_dependency(
    request,
    settings: Settings = Depends(get_config)
):
    """Rate limiting dependency.
    
    This dependency can be used to apply rate limiting to specific endpoints.
    
    Args:
        request: FastAPI request object
        settings: Application settings
    """
    # Rate limiting logic will be implemented with slowapi middleware
    # This is a placeholder for custom rate limiting logic if needed
    pass


# Health check dependencies
async def check_dependencies_health(
    db: AsyncSession = Depends(get_database),
    cache: CacheService = Depends(get_cache)
) -> dict:
    """Check health of all dependencies.
    
    Args:
        db: Database session
        cache: Cache service
        
    Returns:
        Health status of dependencies
    """
    health_status = {
        "database": False,
        "cache": False,
        "overall": False
    }
    
    try:
        # Check database
        await db.execute("SELECT 1")
        health_status["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    try:
        # Check cache
        await cache.redis.ping()
        health_status["cache"] = True
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
    
    # Overall health
    health_status["overall"] = all([
        health_status["database"],
        health_status["cache"]
    ])
    
    return health_status