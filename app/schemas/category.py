"""Category Pydantic schemas for category management.

This module contains all Pydantic models for category-related operations
including CRUD operations, hierarchy management, and responses.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class CategoryBase(BaseModel):
    """Base category schema with common fields."""
    
    name: str = Field(min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=1000, description="Category description")
    image_url: Optional[str] = Field(None, description="Category image URL")
    icon_url: Optional[str] = Field(None, description="Category icon URL")
    meta_title: Optional[str] = Field(None, max_length=200, description="SEO meta title")
    meta_description: Optional[str] = Field(None, max_length=500, description="SEO meta description")
    meta_keywords: Optional[str] = Field(None, max_length=500, description="SEO meta keywords")
    display_order: int = Field(0, description="Display order for sorting")
    is_active: bool = Field(True, description="Whether category is active")
    is_featured: bool = Field(False, description="Whether category is featured")
    
    @validator("name")
    def validate_name(cls, v):
        """Validate category name."""
        if not v.strip():
            raise ValueError("Category name cannot be empty")
        return v.strip()
    
    @validator("display_order")
    def validate_display_order(cls, v):
        """Validate display order."""
        if v < 0:
            raise ValueError("Display order must be non-negative")
        return v


class CategoryCreate(CategoryBase):
    """Schema for category creation."""
    
    parent_id: Optional[str] = Field(None, description="Parent category ID")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Electronics",
                "description": "Electronic devices and accessories",
                "image_url": "https://example.com/electronics.jpg",
                "icon_url": "https://example.com/electronics-icon.svg",
                "meta_title": "Electronics - Best Deals Online",
                "meta_description": "Shop the latest electronics with great prices",
                "meta_keywords": "electronics, gadgets, devices",
                "parent_id": None,
                "display_order": 1,
                "is_active": True,
                "is_featured": True
            }
        }


class CategoryUpdate(BaseModel):
    """Schema for category updates."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=1000, description="Category description")
    image_url: Optional[str] = Field(None, description="Category image URL")
    icon_url: Optional[str] = Field(None, description="Category icon URL")
    meta_title: Optional[str] = Field(None, max_length=200, description="SEO meta title")
    meta_description: Optional[str] = Field(None, max_length=500, description="SEO meta description")
    meta_keywords: Optional[str] = Field(None, max_length=500, description="SEO meta keywords")
    parent_id: Optional[str] = Field(None, description="Parent category ID")
    display_order: Optional[int] = Field(None, description="Display order for sorting")
    is_active: Optional[bool] = Field(None, description="Whether category is active")
    is_featured: Optional[bool] = Field(None, description="Whether category is featured")
    
    @validator("name")
    def validate_name(cls, v):
        """Validate category name."""
        if v is not None and not v.strip():
            raise ValueError("Category name cannot be empty")
        return v.strip() if v else v
    
    @validator("display_order")
    def validate_display_order(cls, v):
        """Validate display order."""
        if v is not None and v < 0:
            raise ValueError("Display order must be non-negative")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Smartphones",
                "description": "Latest smartphones and mobile devices",
                "display_order": 2,
                "is_featured": True
            }
        }


class CategoryMove(BaseModel):
    """Schema for moving category to different parent."""
    
    new_parent_id: Optional[str] = Field(None, description="New parent category ID (null for root)")
    new_position: Optional[int] = Field(None, description="New position in parent")
    
    class Config:
        schema_extra = {
            "example": {
                "new_parent_id": "123e4567-e89b-12d3-a456-426614174000",
                "new_position": 1
            }
        }


class Category(CategoryBase):
    """Schema for category response."""
    
    id: str = Field(description="Category ID")
    slug: str = Field(description="Category slug")
    parent_id: Optional[str] = Field(None, description="Parent category ID")
    product_count: int = Field(description="Number of products in category")
    view_count: int = Field(description="Number of views")
    level: int = Field(description="Category level in hierarchy")
    full_path: str = Field(description="Full category path")
    created_at: datetime = Field(description="Creation time")
    updated_at: datetime = Field(description="Last update time")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Smartphones",
                "slug": "smartphones",
                "description": "Latest smartphones and mobile devices",
                "image_url": "https://example.com/smartphones.jpg",
                "parent_id": "456e7890-e89b-12d3-a456-426614174000",
                "product_count": 150,
                "view_count": 1250,
                "level": 2,
                "full_path": "Electronics > Mobile Devices > Smartphones",
                "display_order": 1,
                "is_active": True,
                "is_featured": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class CategoryWithChildren(Category):
    """Schema for category with children."""
    
    children: List['CategoryWithChildren'] = Field(default_factory=list, description="Child categories")
    
    class Config:
        from_attributes = True


class CategorySummary(BaseModel):
    """Schema for category summary in listings."""
    
    id: str = Field(description="Category ID")
    name: str = Field(description="Category name")
    slug: str = Field(description="Category slug")
    image_url: Optional[str] = Field(None, description="Category image URL")
    icon_url: Optional[str] = Field(None, description="Category icon URL")
    product_count: int = Field(description="Number of products in category")
    level: int = Field(description="Category level in hierarchy")
    is_featured: bool = Field(description="Whether category is featured")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Smartphones",
                "slug": "smartphones",
                "image_url": "https://example.com/smartphones.jpg",
                "icon_url": "https://example.com/smartphone-icon.svg",
                "product_count": 150,
                "level": 2,
                "is_featured": True
            }
        }


class CategoryBreadcrumb(BaseModel):
    """Schema for category breadcrumb."""
    
    id: str = Field(description="Category ID")
    name: str = Field(description="Category name")
    slug: str = Field(description="Category slug")
    level: int = Field(description="Category level")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Electronics",
                "slug": "electronics",
                "level": 1
            }
        }


class CategoryTree(BaseModel):
    """Schema for category tree structure."""
    
    id: str = Field(description="Category ID")
    name: str = Field(description="Category name")
    slug: str = Field(description="Category slug")
    level: int = Field(description="Category level")
    product_count: int = Field(description="Number of products in category")
    is_active: bool = Field(description="Whether category is active")
    children: List['CategoryTree'] = Field(default_factory=list, description="Child categories")
    
    class Config:
        from_attributes = True


class CategoryStats(BaseModel):
    """Schema for category statistics."""
    
    id: str = Field(description="Category ID")
    name: str = Field(description="Category name")
    product_count: int = Field(description="Number of products")
    active_product_count: int = Field(description="Number of active products")
    view_count: int = Field(description="Number of views")
    avg_product_price: Optional[float] = Field(None, description="Average product price")
    min_product_price: Optional[float] = Field(None, description="Minimum product price")
    max_product_price: Optional[float] = Field(None, description="Maximum product price")
    total_revenue: Optional[float] = Field(None, description="Total revenue from category")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Smartphones",
                "product_count": 150,
                "active_product_count": 145,
                "view_count": 1250,
                "avg_product_price": 599.99,
                "min_product_price": 199.99,
                "max_product_price": 1299.99,
                "total_revenue": 89999.85
            }
        }


class CategoryBulkOperation(BaseModel):
    """Schema for bulk category operations."""
    
    category_ids: List[str] = Field(description="List of category IDs")
    operation: str = Field(description="Operation type (activate, deactivate, delete, feature, unfeature)")
    
    @validator("operation")
    def validate_operation(cls, v):
        """Validate operation type."""
        allowed_operations = ["activate", "deactivate", "delete", "feature", "unfeature"]
        if v not in allowed_operations:
            raise ValueError(f"Operation must be one of: {', '.join(allowed_operations)}")
        return v
    
    @validator("category_ids")
    def validate_category_ids(cls, v):
        """Validate category IDs list."""
        if not v:
            raise ValueError("At least one category ID is required")
        if len(v) > 100:
            raise ValueError("Maximum 100 categories allowed per operation")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "category_ids": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "456e7890-e89b-12d3-a456-426614174001"
                ],
                "operation": "activate"
            }
        }


class CategoryImport(BaseModel):
    """Schema for category import."""
    
    name: str = Field(description="Category name")
    parent_name: Optional[str] = Field(None, description="Parent category name")
    description: Optional[str] = Field(None, description="Category description")
    display_order: int = Field(0, description="Display order")
    is_active: bool = Field(True, description="Whether category is active")
    is_featured: bool = Field(False, description="Whether category is featured")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Gaming Laptops",
                "parent_name": "Laptops",
                "description": "High-performance gaming laptops",
                "display_order": 1,
                "is_active": True,
                "is_featured": True
            }
        }


# Update forward references
CategoryWithChildren.model_rebuild()
CategoryTree.model_rebuild()