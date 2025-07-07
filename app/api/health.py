"""Health check API endpoints.

This module provides endpoints for monitoring system health,
including database connectivity, cache status, and overall service health.
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import (
    get_db_session,
    get_cache_service,
    check_dependencies_health
)
from app.schemas.common import HealthCheck
from app.services.cache_service import CacheService

# Create router
router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()


@router.get(
    "/",
    response_model=HealthCheck,
    summary="Basic health check",
    description="Basic health check endpoint"
)
async def health_check() -> HealthCheck:
    """Basic health check.
    
    Returns:
        Basic health status
    """
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        environment=settings.ENVIRONMENT
    )


@router.get(
    "/detailed",
    response_model=Dict[str, Any],
    summary="Detailed health check",
    description="Detailed health check with dependency status"
)
async def detailed_health_check(
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> Dict[str, Any]:
    """Detailed health check with dependency status.
    
    Args:
        db: Database session
        cache: Cache service
        
    Returns:
        Detailed health information
        
    Raises:
        HTTPException: If critical dependencies are unhealthy
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "dependencies": {}
    }
    
    # Check dependencies
    dependency_health = await check_dependencies_health(db, cache)
    health_status["dependencies"] = dependency_health
    
    # Determine overall status
    all_healthy = all(
        dep.get("status") == "healthy" 
        for dep in dependency_health.values()
    )
    
    if not all_healthy:
        health_status["status"] = "unhealthy"
        
        # Check if any critical dependencies are down
        critical_deps = ["database", "cache"]
        critical_unhealthy = any(
            dependency_health.get(dep, {}).get("status") != "healthy"
            for dep in critical_deps
        )
        
        if critical_unhealthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health_status
            )
    
    return health_status


@router.get(
    "/database",
    response_model=Dict[str, Any],
    summary="Database health check",
    description="Check database connectivity and status"
)
async def database_health_check(
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Database health check.
    
    Args:
        db: Database session
        
    Returns:
        Database health information
        
    Raises:
        HTTPException: If database is unhealthy
    """
    try:
        # Test database connection with a simple query
        result = await db.execute("SELECT 1 as health_check")
        row = result.fetchone()
        
        if row and row[0] == 1:
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": {
                    "status": "connected",
                    "url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "***",
                    "response_time_ms": "< 100"  # Simplified for demo
                }
            }
        else:
            raise Exception("Invalid response from database")
            
    except Exception as e:
        error_response = {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "status": "disconnected",
                "error": str(e),
                "url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "***"
            }
        }
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_response
        )


@router.get(
    "/cache",
    response_model=Dict[str, Any],
    summary="Cache health check",
    description="Check cache connectivity and status"
)
async def cache_health_check(
    cache: CacheService = Depends(get_cache_service)
) -> Dict[str, Any]:
    """Cache health check.
    
    Args:
        cache: Cache service
        
    Returns:
        Cache health information
        
    Raises:
        HTTPException: If cache is unhealthy
    """
    try:
        # Test cache connection
        test_key = "health_check_test"
        test_value = "ok"
        
        # Set and get test value
        await cache.set(test_key, test_value, expire=60)
        retrieved_value = await cache.get(test_key)
        
        if retrieved_value == test_value:
            # Clean up test key
            await cache.delete(test_key)
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "cache": {
                    "status": "connected",
                    "url": settings.REDIS_URL.split("@")[-1] if "@" in settings.REDIS_URL else "***",
                    "response_time_ms": "< 50"  # Simplified for demo
                }
            }
        else:
            raise Exception("Cache read/write test failed")
            
    except Exception as e:
        error_response = {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "cache": {
                "status": "disconnected",
                "error": str(e),
                "url": settings.REDIS_URL.split("@")[-1] if "@" in settings.REDIS_URL else "***"
            }
        }
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_response
        )


@router.get(
    "/metrics",
    response_model=Dict[str, Any],
    summary="System metrics",
    description="Get basic system metrics and statistics"
)
async def system_metrics(
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> Dict[str, Any]:
    """Get system metrics.
    
    Args:
        db: Database session
        cache: Cache service
        
    Returns:
        System metrics and statistics
    """
    try:
        # Get basic database statistics
        from app.models.product import Product
        from app.models.category import Category
        from app.models.brand import Brand
        from app.models.user import User
        from sqlalchemy import func, select
        
        # Count records in main tables
        product_count_result = await db.execute(select(func.count()).select_from(Product))
        product_count = product_count_result.scalar()
        
        category_count_result = await db.execute(select(func.count()).select_from(Category))
        category_count = category_count_result.scalar()
        
        brand_count_result = await db.execute(select(func.count()).select_from(Brand))
        brand_count = brand_count_result.scalar()
        
        user_count_result = await db.execute(select(func.count()).select_from(User))
        user_count = user_count_result.scalar()
        
        # Get active counts
        active_product_count_result = await db.execute(
            select(func.count()).where(Product.is_active == True)
        )
        active_product_count = active_product_count_result.scalar()
        
        active_category_count_result = await db.execute(
            select(func.count()).where(Category.is_active == True)
        )
        active_category_count = active_category_count_result.scalar()
        
        active_brand_count_result = await db.execute(
            select(func.count()).where(Brand.is_active == True)
        )
        active_brand_count = active_brand_count_result.scalar()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "metrics": {
                "database": {
                    "total_products": product_count,
                    "active_products": active_product_count,
                    "total_categories": category_count,
                    "active_categories": active_category_count,
                    "total_brands": brand_count,
                    "active_brands": active_brand_count,
                    "total_users": user_count
                },
                "cache": {
                    "status": "connected",
                    "type": "redis"
                },
                "system": {
                    "uptime": "N/A",  # Would need to track application start time
                    "memory_usage": "N/A",  # Would need psutil or similar
                    "cpu_usage": "N/A"  # Would need psutil or similar
                }
            }
        }
        
    except Exception as e:
        return {
            "status": "partial",
            "timestamp": datetime.utcnow().isoformat(),
            "error": f"Failed to collect some metrics: {str(e)}",
            "metrics": {
                "database": "error",
                "cache": "unknown",
                "system": "unknown"
            }
        }


@router.get(
    "/readiness",
    response_model=Dict[str, Any],
    summary="Readiness probe",
    description="Kubernetes readiness probe endpoint"
)
async def readiness_probe(
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> Dict[str, Any]:
    """Readiness probe for Kubernetes.
    
    Args:
        db: Database session
        cache: Cache service
        
    Returns:
        Readiness status
        
    Raises:
        HTTPException: If service is not ready
    """
    try:
        # Check critical dependencies
        dependency_health = await check_dependencies_health(db, cache)
        
        # Service is ready if database and cache are healthy
        db_healthy = dependency_health.get("database", {}).get("status") == "healthy"
        cache_healthy = dependency_health.get("cache", {}).get("status") == "healthy"
        
        if db_healthy and cache_healthy:
            return {
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat(),
                "dependencies": dependency_health
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "not_ready",
                    "timestamp": datetime.utcnow().isoformat(),
                    "dependencies": dependency_health
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )


@router.get(
    "/liveness",
    response_model=Dict[str, Any],
    summary="Liveness probe",
    description="Kubernetes liveness probe endpoint"
)
async def liveness_probe() -> Dict[str, Any]:
    """Liveness probe for Kubernetes.
    
    Returns:
        Liveness status
    """
    # Simple liveness check - if this endpoint responds, the service is alive
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }