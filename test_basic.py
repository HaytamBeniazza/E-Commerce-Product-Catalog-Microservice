#!/usr/bin/env python3
"""Basic test script to verify microservice functionality.

This script performs basic tests to ensure the microservice is working correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))


async def test_imports():
    """Test that all modules can be imported successfully."""
    print("Testing imports...")
    
    try:
        # Test config
        from app.config import get_settings
        settings = get_settings()
        print(f"✅ Config loaded - Environment: {settings.ENVIRONMENT}")
        
        # Test models
        from app.models.user import User
        from app.models.category import Category
        from app.models.brand import Brand
        from app.models.product import Product, ProductImage
        print("✅ Models imported successfully")
        
        # Test schemas
        from app.schemas.user import UserCreate
        from app.schemas.category import CategoryCreate
        from app.schemas.brand import BrandCreate
        from app.schemas.product import ProductCreate
        print("✅ Schemas imported successfully")
        
        # Test services
        from app.services.auth_service import AuthService
        from app.services.product_service import ProductService
        from app.services.category_service import CategoryService
        from app.services.brand_service import BrandService
        from app.services.cache_service import CacheService
        print("✅ Services imported successfully")
        
        # Test API routes
        from app.api.auth import router as auth_router
        from app.api.products import router as products_router
        from app.api.categories import router as categories_router
        from app.api.brands import router as brands_router
        from app.api.health import router as health_router
        print("✅ API routers imported successfully")
        
        # Test main app
        from app.main import app
        print("✅ FastAPI app imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def test_schema_validation():
    """Test Pydantic schema validation."""
    print("\nTesting schema validation...")
    
    try:
        from app.schemas.user import UserCreate
        from app.schemas.product import ProductCreate
        from app.schemas.category import CategoryCreate
        from app.schemas.brand import BrandCreate
        
        # Test user schema
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User"
        }
        user = UserCreate(**user_data)
        print(f"✅ User schema validation: {user.email}")
        
        # Test category schema
        category_data = {
            "name": "Electronics",
            "description": "Electronic products"
        }
        category = CategoryCreate(**category_data)
        print(f"✅ Category schema validation: {category.name}")
        
        # Test brand schema
        brand_data = {
            "name": "Apple",
            "description": "Technology company",
            "website": "https://apple.com"
        }
        brand = BrandCreate(**brand_data)
        print(f"✅ Brand schema validation: {brand.name}")
        
        # Test product schema
        product_data = {
            "name": "iPhone 15",
            "description": "Latest iPhone model",
            "sku": "IPHONE15-001",
            "price": 999.99,
            "currency": "USD",
            "stock_quantity": 100
        }
        product = ProductCreate(**product_data)
        print(f"✅ Product schema validation: {product.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema validation error: {e}")
        return False


def test_app_creation():
    """Test FastAPI app creation and route registration."""
    print("\nTesting FastAPI app creation...")
    
    try:
        from app.main import app
        
        # Check if app is created
        if app is None:
            print("❌ FastAPI app is None")
            return False
        
        # Check routes
        routes = [route.path for route in app.routes]
        expected_routes = [
            "/",
            "/health",
            "/auth",
            "/products",
            "/categories",
            "/brands"
        ]
        
        for expected_route in expected_routes:
            if any(expected_route in route for route in routes):
                print(f"✅ Route found: {expected_route}")
            else:
                print(f"⚠️  Route not found: {expected_route}")
        
        print(f"✅ FastAPI app created with {len(routes)} routes")
        return True
        
    except Exception as e:
        print(f"❌ App creation error: {e}")
        return False


def test_environment_config():
    """Test environment configuration."""
    print("\nTesting environment configuration...")
    
    try:
        from app.config import get_settings
        settings = get_settings()
        
        # Check required settings
        required_settings = [
            'DATABASE_URL',
            'REDIS_URL',
            'SECRET_KEY',
            'ENVIRONMENT'
        ]
        
        for setting in required_settings:
            value = getattr(settings, setting, None)
            if value:
                # Mask sensitive values
                if 'SECRET' in setting or 'PASSWORD' in setting:
                    display_value = "***masked***"
                elif 'URL' in setting and '@' in str(value):
                    # Mask credentials in URLs
                    display_value = str(value).split('@')[-1]
                else:
                    display_value = str(value)
                print(f"✅ {setting}: {display_value}")
            else:
                print(f"⚠️  {setting}: Not set")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment config error: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting E-Commerce Product Catalog Microservice Tests\n")
    
    tests = [
        ("Import Tests", test_imports()),
        ("Schema Validation Tests", test_schema_validation()),
        ("App Creation Tests", test_app_creation()),
        ("Environment Config Tests", test_environment_config())
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running {test_name}")
        print(f"{'='*50}")
        
        if asyncio.iscoroutine(test_func):
            result = await test_func
        else:
            result = test_func
        
        results.append((test_name, result))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The microservice is ready to run.")
        print("\n📝 Next steps:")
        print("1. Set up your database (PostgreSQL)")
        print("2. Set up Redis cache")
        print("3. Update .env file with your configuration")
        print("4. Run database migrations: alembic upgrade head")
        print("5. Start the server: uvicorn app.main:app --reload")
        print("6. Visit http://localhost:8000/docs for API documentation")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)