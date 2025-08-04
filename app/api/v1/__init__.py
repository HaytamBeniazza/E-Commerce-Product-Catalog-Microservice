"""API v1 router module.

This module creates the main API router that includes all v1 endpoints.
"""

from fastapi import APIRouter

from app.api import auth, brands, categories, health, products

# Create the main API router
api_router = APIRouter()

# Include all routers with their respective prefixes
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(brands.router, prefix="/brands", tags=["Brands"]) 