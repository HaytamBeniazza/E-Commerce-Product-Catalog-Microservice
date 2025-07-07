"""Product Pydantic schemas for product management.

This module contains all Pydantic models for product-related operations
including CRUD operations, product information, images, and responses.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.models.product import ProductStatus, ProductType


class ProductImageBase(BaseModel):
    """Base product image schema."""
    
    url: str = Field(description="Image URL")
    alt_text: Optional[str] = Field(None, max_length=200, description="Alt text for accessibility")
    display_order: int = Field(0, description="Display order for sorting")
    is_primary: bool = Field(False, description="Whether this is the primary image")
    
    @validator("display_order")
    def validate_display_order(cls, v):
        """Validate display order."""
        if v < 0:
            raise ValueError("Display order must be non-negative")
        return v


class ProductImageCreate(ProductImageBase):
    """Schema for product image creation."""
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com/product-image.jpg",
                "alt_text": "iPhone 15 Pro front view",
                "display_order": 1,
                "is_primary": True
            }
        }


class ProductImageUpdate(BaseModel):
    """Schema for product image updates."""
    
    url: Optional[str] = Field(None, description="Image URL")
    alt_text: Optional[str] = Field(None, max_length=200, description="Alt text for accessibility")
    display_order: Optional[int] = Field(None, description="Display order for sorting")
    is_primary: Optional[bool] = Field(None, description="Whether this is the primary image")
    
    @validator("display_order")
    def validate_display_order(cls, v):
        """Validate display order."""
        if v is not None and v < 0:
            raise ValueError("Display order must be non-negative")
        return v


class ProductImage(ProductImageBase):
    """Schema for product image response."""
    
    id: str = Field(description="Image ID")
    product_id: str = Field(description="Product ID")
    created_at: datetime = Field(description="Creation time")
    updated_at: datetime = Field(description="Last update time")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "product_id": "456e7890-e89b-12d3-a456-426614174001",
                "url": "https://example.com/product-image.jpg",
                "alt_text": "iPhone 15 Pro front view",
                "display_order": 1,
                "is_primary": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class ProductBase(BaseModel):
    """Base product schema with common fields."""
    
    name: str = Field(min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, max_length=2000, description="Product description")
    short_description: Optional[str] = Field(None, max_length=500, description="Short product description")
    sku: str = Field(min_length=1, max_length=100, description="Stock Keeping Unit")
    barcode: Optional[str] = Field(None, max_length=50, description="Product barcode")
    price: Decimal = Field(gt=0, description="Product price")
    compare_price: Optional[Decimal] = Field(None, description="Compare at price for discounts")
    cost_price: Optional[Decimal] = Field(None, description="Cost price for profit calculations")
    currency: str = Field("USD", max_length=3, description="Currency code")
    weight: Optional[Decimal] = Field(None, description="Product weight in kg")
    dimensions: Optional[Dict[str, Decimal]] = Field(None, description="Product dimensions (length, width, height)")
    stock_quantity: int = Field(ge=0, description="Available stock quantity")
    low_stock_threshold: int = Field(10, ge=0, description="Low stock alert threshold")
    track_inventory: bool = Field(True, description="Whether to track inventory")
    allow_backorder: bool = Field(False, description="Whether to allow backorders")
    product_type: ProductType = Field(ProductType.SIMPLE, description="Product type")
    status: ProductStatus = Field(ProductStatus.DRAFT, description="Product status")
    is_featured: bool = Field(False, description="Whether product is featured")
    is_digital: bool = Field(False, description="Whether product is digital")
    requires_shipping: bool = Field(True, description="Whether product requires shipping")
    meta_title: Optional[str] = Field(None, max_length=200, description="SEO meta title")
    meta_description: Optional[str] = Field(None, max_length=500, description="SEO meta description")
    meta_keywords: Optional[str] = Field(None, max_length=500, description="SEO meta keywords")
    tags: List[str] = Field(default_factory=list, description="Product tags")
    attributes: Dict[str, str] = Field(default_factory=dict, description="Product attributes")
    
    @validator("name")
    def validate_name(cls, v):
        """Validate product name."""
        if not v.strip():
            raise ValueError("Product name cannot be empty")
        return v.strip()
    
    @validator("sku")
    def validate_sku(cls, v):
        """Validate SKU format."""
        if not v.strip():
            raise ValueError("SKU cannot be empty")
        # Allow alphanumeric, hyphens, and underscores
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("SKU can only contain letters, numbers, hyphens, and underscores")
        return v.upper().strip()
    
    @validator("currency")
    def validate_currency(cls, v):
        """Validate currency code."""
        if len(v) != 3 or not v.isalpha():
            raise ValueError("Currency must be a 3-letter code")
        return v.upper()
    
    @validator("compare_price")
    def validate_compare_price(cls, v, values):
        """Validate compare price."""
        if v is not None and "price" in values and v <= values["price"]:
            raise ValueError("Compare price must be greater than regular price")
        return v
    
    @validator("cost_price")
    def validate_cost_price(cls, v, values):
        """Validate cost price."""
        if v is not None and "price" in values and v >= values["price"]:
            raise ValueError("Cost price should be less than selling price")
        return v
    
    @validator("dimensions")
    def validate_dimensions(cls, v):
        """Validate product dimensions."""
        if v:
            required_keys = {"length", "width", "height"}
            if not required_keys.issubset(v.keys()):
                raise ValueError("Dimensions must include length, width, and height")
            for key, value in v.items():
                if value <= 0:
                    raise ValueError(f"Dimension {key} must be positive")
        return v
    
    @validator("tags")
    def validate_tags(cls, v):
        """Validate product tags."""
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        return [tag.strip().lower() for tag in v if tag.strip()]


class ProductCreate(ProductBase):
    """Schema for product creation."""
    
    category_ids: List[str] = Field(description="List of category IDs")
    brand_id: Optional[str] = Field(None, description="Brand ID")
    images: List[ProductImageCreate] = Field(default_factory=list, description="Product images")
    
    @validator("category_ids")
    def validate_category_ids(cls, v):
        """Validate category IDs."""
        if not v:
            raise ValueError("At least one category is required")
        if len(v) > 10:
            raise ValueError("Maximum 10 categories allowed")
        return v
    
    @validator("images")
    def validate_images(cls, v):
        """Validate product images."""
        if len(v) > 20:
            raise ValueError("Maximum 20 images allowed")
        
        primary_count = sum(1 for img in v if img.is_primary)
        if primary_count > 1:
            raise ValueError("Only one image can be marked as primary")
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "iPhone 15 Pro",
                "description": "The latest iPhone with advanced features",
                "short_description": "Latest iPhone with Pro features",
                "sku": "IPHONE-15-PRO-128",
                "barcode": "1234567890123",
                "price": 999.99,
                "compare_price": 1099.99,
                "cost_price": 600.00,
                "currency": "USD",
                "weight": 0.187,
                "dimensions": {
                    "length": 14.67,
                    "width": 7.09,
                    "height": 0.83
                },
                "stock_quantity": 100,
                "low_stock_threshold": 10,
                "track_inventory": True,
                "allow_backorder": False,
                "product_type": "simple",
                "status": "active",
                "is_featured": True,
                "is_digital": False,
                "requires_shipping": True,
                "meta_title": "iPhone 15 Pro - Latest Apple Smartphone",
                "meta_description": "Get the latest iPhone 15 Pro with advanced features",
                "meta_keywords": "iphone, apple, smartphone, mobile",
                "category_ids": ["123e4567-e89b-12d3-a456-426614174000"],
                "brand_id": "456e7890-e89b-12d3-a456-426614174001",
                "tags": ["smartphone", "apple", "premium"],
                "attributes": {
                    "color": "Space Black",
                    "storage": "128GB",
                    "screen_size": "6.1 inch"
                }
            }
        }


class ProductUpdate(BaseModel):
    """Schema for product updates."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, max_length=2000, description="Product description")
    short_description: Optional[str] = Field(None, max_length=500, description="Short product description")
    sku: Optional[str] = Field(None, min_length=1, max_length=100, description="Stock Keeping Unit")
    barcode: Optional[str] = Field(None, max_length=50, description="Product barcode")
    price: Optional[Decimal] = Field(None, gt=0, description="Product price")
    compare_price: Optional[Decimal] = Field(None, description="Compare at price for discounts")
    cost_price: Optional[Decimal] = Field(None, description="Cost price for profit calculations")
    currency: Optional[str] = Field(None, max_length=3, description="Currency code")
    weight: Optional[Decimal] = Field(None, description="Product weight in kg")
    dimensions: Optional[Dict[str, Decimal]] = Field(None, description="Product dimensions")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Available stock quantity")
    low_stock_threshold: Optional[int] = Field(None, ge=0, description="Low stock alert threshold")
    track_inventory: Optional[bool] = Field(None, description="Whether to track inventory")
    allow_backorder: Optional[bool] = Field(None, description="Whether to allow backorders")
    product_type: Optional[ProductType] = Field(None, description="Product type")
    status: Optional[ProductStatus] = Field(None, description="Product status")
    is_featured: Optional[bool] = Field(None, description="Whether product is featured")
    is_digital: Optional[bool] = Field(None, description="Whether product is digital")
    requires_shipping: Optional[bool] = Field(None, description="Whether product requires shipping")
    meta_title: Optional[str] = Field(None, max_length=200, description="SEO meta title")
    meta_description: Optional[str] = Field(None, max_length=500, description="SEO meta description")
    meta_keywords: Optional[str] = Field(None, max_length=500, description="SEO meta keywords")
    category_ids: Optional[List[str]] = Field(None, description="List of category IDs")
    brand_id: Optional[str] = Field(None, description="Brand ID")
    tags: Optional[List[str]] = Field(None, description="Product tags")
    attributes: Optional[Dict[str, str]] = Field(None, description="Product attributes")
    
    # Apply same validators as ProductBase for non-None values
    @validator("name")
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Product name cannot be empty")
        return v.strip() if v else v
    
    @validator("sku")
    def validate_sku(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("SKU cannot be empty")
            if not v.replace("-", "").replace("_", "").isalnum():
                raise ValueError("SKU can only contain letters, numbers, hyphens, and underscores")
            return v.upper().strip()
        return v
    
    @validator("currency")
    def validate_currency(cls, v):
        if v is not None:
            if len(v) != 3 or not v.isalpha():
                raise ValueError("Currency must be a 3-letter code")
            return v.upper()
        return v
    
    @validator("category_ids")
    def validate_category_ids(cls, v):
        if v is not None:
            if not v:
                raise ValueError("At least one category is required")
            if len(v) > 10:
                raise ValueError("Maximum 10 categories allowed")
        return v
    
    @validator("tags")
    def validate_tags(cls, v):
        if v is not None:
            if len(v) > 20:
                raise ValueError("Maximum 20 tags allowed")
            return [tag.strip().lower() for tag in v if tag.strip()]
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "iPhone 15 Pro Max",
                "price": 1199.99,
                "stock_quantity": 50,
                "is_featured": True,
                "status": "active"
            }
        }


class Product(ProductBase):
    """Schema for product response."""
    
    id: str = Field(description="Product ID")
    slug: str = Field(description="Product slug")
    category_ids: List[str] = Field(description="List of category IDs")
    brand_id: Optional[str] = Field(None, description="Brand ID")
    view_count: int = Field(description="Number of views")
    rating: float = Field(description="Average product rating")
    review_count: int = Field(description="Number of reviews")
    sales_count: int = Field(description="Number of sales")
    images: List[ProductImage] = Field(default_factory=list, description="Product images")
    created_at: datetime = Field(description="Creation time")
    updated_at: datetime = Field(description="Last update time")
    
    # Computed fields
    is_in_stock: bool = Field(description="Whether product is in stock")
    is_low_stock: bool = Field(description="Whether product is low in stock")
    discount_percentage: Optional[float] = Field(None, description="Discount percentage")
    profit_margin: Optional[float] = Field(None, description="Profit margin percentage")
    primary_image: Optional[ProductImage] = Field(None, description="Primary product image")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "iPhone 15 Pro",
                "slug": "iphone-15-pro",
                "description": "The latest iPhone with advanced features",
                "sku": "IPHONE-15-PRO-128",
                "price": 999.99,
                "compare_price": 1099.99,
                "currency": "USD",
                "stock_quantity": 100,
                "product_type": "simple",
                "status": "active",
                "is_featured": True,
                "view_count": 1500,
                "rating": 4.5,
                "review_count": 125,
                "sales_count": 50,
                "is_in_stock": True,
                "is_low_stock": False,
                "discount_percentage": 9.1,
                "profit_margin": 40.0,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class ProductSummary(BaseModel):
    """Schema for product summary in listings."""
    
    id: str = Field(description="Product ID")
    name: str = Field(description="Product name")
    slug: str = Field(description="Product slug")
    sku: str = Field(description="Stock Keeping Unit")
    price: Decimal = Field(description="Product price")
    compare_price: Optional[Decimal] = Field(None, description="Compare at price")
    currency: str = Field(description="Currency code")
    stock_quantity: int = Field(description="Available stock quantity")
    status: ProductStatus = Field(description="Product status")
    is_featured: bool = Field(description="Whether product is featured")
    rating: float = Field(description="Average product rating")
    review_count: int = Field(description="Number of reviews")
    primary_image: Optional[str] = Field(None, description="Primary image URL")
    is_in_stock: bool = Field(description="Whether product is in stock")
    discount_percentage: Optional[float] = Field(None, description="Discount percentage")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "iPhone 15 Pro",
                "slug": "iphone-15-pro",
                "sku": "IPHONE-15-PRO-128",
                "price": 999.99,
                "compare_price": 1099.99,
                "currency": "USD",
                "stock_quantity": 100,
                "status": "active",
                "is_featured": True,
                "rating": 4.5,
                "review_count": 125,
                "primary_image": "https://example.com/iphone-15-pro.jpg",
                "is_in_stock": True,
                "discount_percentage": 9.1
            }
        }


class ProductStats(BaseModel):
    """Schema for product statistics."""
    
    id: str = Field(description="Product ID")
    name: str = Field(description="Product name")
    view_count: int = Field(description="Number of views")
    sales_count: int = Field(description="Number of sales")
    revenue: Decimal = Field(description="Total revenue")
    rating: float = Field(description="Average rating")
    review_count: int = Field(description="Number of reviews")
    conversion_rate: float = Field(description="View to sale conversion rate")
    profit: Optional[Decimal] = Field(None, description="Total profit")
    profit_margin: Optional[float] = Field(None, description="Profit margin percentage")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "iPhone 15 Pro",
                "view_count": 1500,
                "sales_count": 50,
                "revenue": 49999.50,
                "rating": 4.5,
                "review_count": 125,
                "conversion_rate": 3.33,
                "profit": 19999.50,
                "profit_margin": 40.0
            }
        }


class ProductBulkOperation(BaseModel):
    """Schema for bulk product operations."""
    
    product_ids: List[str] = Field(description="List of product IDs")
    operation: str = Field(description="Operation type (activate, deactivate, delete, feature, unfeature, update_stock)")
    data: Optional[Dict] = Field(None, description="Additional data for the operation")
    
    @validator("operation")
    def validate_operation(cls, v):
        """Validate operation type."""
        allowed_operations = ["activate", "deactivate", "delete", "feature", "unfeature", "update_stock", "update_price"]
        if v not in allowed_operations:
            raise ValueError(f"Operation must be one of: {', '.join(allowed_operations)}")
        return v
    
    @validator("product_ids")
    def validate_product_ids(cls, v):
        """Validate product IDs list."""
        if not v:
            raise ValueError("At least one product ID is required")
        if len(v) > 100:
            raise ValueError("Maximum 100 products allowed per operation")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "product_ids": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "456e7890-e89b-12d3-a456-426614174001"
                ],
                "operation": "update_stock",
                "data": {
                    "stock_quantity": 50
                }
            }
        }


class ProductImport(BaseModel):
    """Schema for product import."""
    
    name: str = Field(description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    sku: str = Field(description="Stock Keeping Unit")
    price: Decimal = Field(description="Product price")
    cost_price: Optional[Decimal] = Field(None, description="Cost price")
    stock_quantity: int = Field(description="Stock quantity")
    category_names: List[str] = Field(description="Category names")
    brand_name: Optional[str] = Field(None, description="Brand name")
    tags: List[str] = Field(default_factory=list, description="Product tags")
    attributes: Dict[str, str] = Field(default_factory=dict, description="Product attributes")
    is_active: bool = Field(True, description="Whether product is active")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Samsung Galaxy S24",
                "description": "Latest Samsung flagship smartphone",
                "sku": "GALAXY-S24-256",
                "price": 899.99,
                "cost_price": 550.00,
                "stock_quantity": 75,
                "category_names": ["Electronics", "Smartphones"],
                "brand_name": "Samsung",
                "tags": ["smartphone", "android", "flagship"],
                "attributes": {
                    "color": "Phantom Black",
                    "storage": "256GB",
                    "ram": "8GB"
                },
                "is_active": True
            }
        }


class ProductSearch(BaseModel):
    """Schema for product search filters."""
    
    query: Optional[str] = Field(None, description="Search query")
    category_ids: Optional[List[str]] = Field(None, description="Filter by category IDs")
    brand_ids: Optional[List[str]] = Field(None, description="Filter by brand IDs")
    min_price: Optional[Decimal] = Field(None, description="Minimum price filter")
    max_price: Optional[Decimal] = Field(None, description="Maximum price filter")
    in_stock_only: bool = Field(False, description="Show only in-stock products")
    featured_only: bool = Field(False, description="Show only featured products")
    status: Optional[ProductStatus] = Field(None, description="Filter by status")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    attributes: Optional[Dict[str, str]] = Field(None, description="Filter by attributes")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc, desc)")
    
    @validator("sort_by")
    def validate_sort_by(cls, v):
        """Validate sort field."""
        allowed_fields = ["name", "price", "created_at", "updated_at", "rating", "sales_count", "view_count"]
        if v not in allowed_fields:
            raise ValueError(f"Sort field must be one of: {', '.join(allowed_fields)}")
        return v
    
    @validator("sort_order")
    def validate_sort_order(cls, v):
        """Validate sort order."""
        if v not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "query": "smartphone",
                "category_ids": ["123e4567-e89b-12d3-a456-426614174000"],
                "brand_ids": ["456e7890-e89b-12d3-a456-426614174001"],
                "min_price": 100.00,
                "max_price": 1500.00,
                "in_stock_only": True,
                "featured_only": False,
                "status": "active",
                "tags": ["premium"],
                "sort_by": "price",
                "sort_order": "asc"
            }
        }