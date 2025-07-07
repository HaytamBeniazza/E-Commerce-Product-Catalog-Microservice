#!/usr/bin/env python3
"""Demo script to showcase the E-Commerce Product Catalog Microservice.

This script demonstrates the microservice functionality without requiring
external dependencies like PostgreSQL or Redis.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn


def create_demo_app():
    """Create a demo FastAPI app without database dependencies."""
    
    app = FastAPI(
        title="E-Commerce Product Catalog Microservice",
        description="A comprehensive e-commerce product catalog microservice",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Welcome to E-Commerce Product Catalog Microservice",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "E-Commerce Product Catalog",
            "version": "1.0.0",
            "timestamp": "2024-01-01T00:00:00Z",
            "environment": "demo"
        }
    
    @app.get("/api/v1/products")
    async def get_products():
        """Demo products endpoint."""
        return {
            "products": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "iPhone 15 Pro",
                    "description": "Latest iPhone with advanced features",
                    "price": 999.99,
                    "currency": "USD",
                    "sku": "IPHONE-15-PRO-128",
                    "stock_quantity": 100,
                    "status": "active",
                    "is_featured": True,
                    "category": "Electronics",
                    "brand": "Apple"
                },
                {
                    "id": "456e7890-e89b-12d3-a456-426614174001",
                    "name": "Samsung Galaxy S24",
                    "description": "Premium Android smartphone",
                    "price": 899.99,
                    "currency": "USD",
                    "sku": "GALAXY-S24-256",
                    "stock_quantity": 75,
                    "status": "active",
                    "is_featured": True,
                    "category": "Electronics",
                    "brand": "Samsung"
                }
            ],
            "total": 2,
            "page": 1,
            "per_page": 20
        }
    
    @app.get("/api/v1/categories")
    async def get_categories():
        """Demo categories endpoint."""
        return {
            "categories": [
                {
                    "id": "789e0123-e89b-12d3-a456-426614174002",
                    "name": "Electronics",
                    "slug": "electronics",
                    "description": "Electronic devices and gadgets",
                    "product_count": 150,
                    "is_active": True,
                    "is_featured": True
                },
                {
                    "id": "012e3456-e89b-12d3-a456-426614174003",
                    "name": "Clothing",
                    "slug": "clothing",
                    "description": "Fashion and apparel",
                    "product_count": 200,
                    "is_active": True,
                    "is_featured": False
                }
            ],
            "total": 2
        }
    
    @app.get("/api/v1/brands")
    async def get_brands():
        """Demo brands endpoint."""
        return {
            "brands": [
                {
                    "id": "345e6789-e89b-12d3-a456-426614174004",
                    "name": "Apple",
                    "slug": "apple",
                    "description": "Technology company known for innovative products",
                    "website": "https://www.apple.com",
                    "product_count": 50,
                    "rating": 4.5,
                    "is_featured": True,
                    "is_verified": True
                },
                {
                    "id": "678e9012-e89b-12d3-a456-426614174005",
                    "name": "Samsung",
                    "slug": "samsung",
                    "description": "South Korean multinational electronics company",
                    "website": "https://www.samsung.com",
                    "product_count": 75,
                    "rating": 4.3,
                    "is_featured": True,
                    "is_verified": True
                }
            ],
            "total": 2
        }
    
    @app.get("/api/v1/auth/me")
    async def get_current_user():
        """Demo current user endpoint."""
        return {
            "message": "Authentication required",
            "note": "This is a demo endpoint. In production, this would return the current user's information."
        }
    
    return app


def main():
    """Run the demo application."""
    print("🚀 Starting E-Commerce Product Catalog Microservice Demo")
    print("📝 This is a demonstration version without database dependencies")
    print("🔗 API Documentation will be available at: http://localhost:8000/docs")
    print("🔗 ReDoc Documentation will be available at: http://localhost:8000/redoc")
    print("\n📋 Available Demo Endpoints:")
    print("   GET /                     - Root endpoint")
    print("   GET /health               - Health check")
    print("   GET /api/v1/products      - List products")
    print("   GET /api/v1/categories    - List categories")
    print("   GET /api/v1/brands        - List brands")
    print("   GET /api/v1/auth/me       - Current user (demo)")
    print("\n⚠️  Note: This demo doesn't include database operations.")
    print("   For full functionality, set up PostgreSQL and Redis as described in README.md")
    print("\n" + "="*70)
    
    app = create_demo_app()
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Demo stopped. Thank you for trying the E-Commerce Product Catalog Microservice!")
    except Exception as e:
        print(f"\n❌ Error starting demo: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)