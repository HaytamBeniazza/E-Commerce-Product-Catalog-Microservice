"""Brand Pydantic schemas for brand management.

This module contains all Pydantic models for brand-related operations
including CRUD operations, brand information, and responses.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, validator


class BrandBase(BaseModel):
    """Base brand schema with common fields."""
    
    name: str = Field(min_length=1, max_length=100, description="Brand name")
    description: Optional[str] = Field(None, max_length=1000, description="Brand description")
    website: Optional[HttpUrl] = Field(None, description="Brand website URL")
    email: Optional[str] = Field(None, description="Brand contact email")
    phone: Optional[str] = Field(None, max_length=20, description="Brand contact phone")
    logo_url: Optional[str] = Field(None, description="Brand logo URL")
    banner_url: Optional[str] = Field(None, description="Brand banner URL")
    company_name: Optional[str] = Field(None, max_length=200, description="Company name")
    founded_year: Optional[int] = Field(None, description="Year company was founded")
    country: Optional[str] = Field(None, max_length=100, description="Country of origin")
    meta_title: Optional[str] = Field(None, max_length=200, description="SEO meta title")
    meta_description: Optional[str] = Field(None, max_length=500, description="SEO meta description")
    meta_keywords: Optional[str] = Field(None, max_length=500, description="SEO meta keywords")
    display_order: int = Field(0, description="Display order for sorting")
    is_active: bool = Field(True, description="Whether brand is active")
    is_featured: bool = Field(False, description="Whether brand is featured")
    is_verified: bool = Field(False, description="Whether brand is verified")
    
    @validator("name")
    def validate_name(cls, v):
        """Validate brand name."""
        if not v.strip():
            raise ValueError("Brand name cannot be empty")
        return v.strip()
    
    @validator("founded_year")
    def validate_founded_year(cls, v):
        """Validate founded year."""
        if v is not None:
            current_year = datetime.now().year
            if v < 1800 or v > current_year:
                raise ValueError(f"Founded year must be between 1800 and {current_year}")
        return v
    
    @validator("display_order")
    def validate_display_order(cls, v):
        """Validate display order."""
        if v < 0:
            raise ValueError("Display order must be non-negative")
        return v
    
    @validator("email")
    def validate_email(cls, v):
        """Validate email format."""
        if v and "@" not in v:
            raise ValueError("Invalid email format")
        return v
    
    @validator("phone")
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v and not v.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "").isdigit():
            raise ValueError("Invalid phone number format")
        return v


class BrandCreate(BrandBase):
    """Schema for brand creation."""
    
    social_media: Optional[Dict[str, str]] = Field(None, description="Social media links")
    
    @validator("social_media")
    def validate_social_media(cls, v):
        """Validate social media links."""
        if v:
            allowed_platforms = ["facebook", "twitter", "instagram", "linkedin", "youtube", "tiktok"]
            for platform in v.keys():
                if platform not in allowed_platforms:
                    raise ValueError(f"Unsupported social media platform: {platform}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Apple",
                "description": "Technology company known for innovative products",
                "website": "https://www.apple.com",
                "email": "contact@apple.com",
                "phone": "+1-800-275-2273",
                "logo_url": "https://example.com/apple-logo.png",
                "banner_url": "https://example.com/apple-banner.jpg",
                "company_name": "Apple Inc.",
                "founded_year": 1976,
                "country": "United States",
                "meta_title": "Apple - Innovation at its finest",
                "meta_description": "Discover Apple's innovative products and services",
                "meta_keywords": "apple, iphone, ipad, mac, technology",
                "display_order": 1,
                "is_active": True,
                "is_featured": True,
                "is_verified": True,
                "social_media": {
                    "facebook": "https://facebook.com/apple",
                    "twitter": "https://twitter.com/apple",
                    "instagram": "https://instagram.com/apple"
                }
            }
        }


class BrandUpdate(BaseModel):
    """Schema for brand updates."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Brand name")
    description: Optional[str] = Field(None, max_length=1000, description="Brand description")
    website: Optional[HttpUrl] = Field(None, description="Brand website URL")
    email: Optional[str] = Field(None, description="Brand contact email")
    phone: Optional[str] = Field(None, max_length=20, description="Brand contact phone")
    logo_url: Optional[str] = Field(None, description="Brand logo URL")
    banner_url: Optional[str] = Field(None, description="Brand banner URL")
    company_name: Optional[str] = Field(None, max_length=200, description="Company name")
    founded_year: Optional[int] = Field(None, description="Year company was founded")
    country: Optional[str] = Field(None, max_length=100, description="Country of origin")
    meta_title: Optional[str] = Field(None, max_length=200, description="SEO meta title")
    meta_description: Optional[str] = Field(None, max_length=500, description="SEO meta description")
    meta_keywords: Optional[str] = Field(None, max_length=500, description="SEO meta keywords")
    display_order: Optional[int] = Field(None, description="Display order for sorting")
    is_active: Optional[bool] = Field(None, description="Whether brand is active")
    is_featured: Optional[bool] = Field(None, description="Whether brand is featured")
    is_verified: Optional[bool] = Field(None, description="Whether brand is verified")
    social_media: Optional[Dict[str, str]] = Field(None, description="Social media links")
    
    @validator("name")
    def validate_name(cls, v):
        """Validate brand name."""
        if v is not None and not v.strip():
            raise ValueError("Brand name cannot be empty")
        return v.strip() if v else v
    
    @validator("founded_year")
    def validate_founded_year(cls, v):
        """Validate founded year."""
        if v is not None:
            current_year = datetime.now().year
            if v < 1800 or v > current_year:
                raise ValueError(f"Founded year must be between 1800 and {current_year}")
        return v
    
    @validator("display_order")
    def validate_display_order(cls, v):
        """Validate display order."""
        if v is not None and v < 0:
            raise ValueError("Display order must be non-negative")
        return v
    
    @validator("email")
    def validate_email(cls, v):
        """Validate email format."""
        if v and "@" not in v:
            raise ValueError("Invalid email format")
        return v
    
    @validator("phone")
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v and not v.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "").isdigit():
            raise ValueError("Invalid phone number format")
        return v
    
    @validator("social_media")
    def validate_social_media(cls, v):
        """Validate social media links."""
        if v:
            allowed_platforms = ["facebook", "twitter", "instagram", "linkedin", "youtube", "tiktok"]
            for platform in v.keys():
                if platform not in allowed_platforms:
                    raise ValueError(f"Unsupported social media platform: {platform}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Apple Inc.",
                "description": "Leading technology company",
                "website": "https://www.apple.com",
                "is_featured": True,
                "social_media": {
                    "twitter": "https://twitter.com/apple",
                    "instagram": "https://instagram.com/apple"
                }
            }
        }


class Brand(BrandBase):
    """Schema for brand response."""
    
    id: str = Field(description="Brand ID")
    slug: str = Field(description="Brand slug")
    product_count: int = Field(description="Number of products from this brand")
    view_count: int = Field(description="Number of views")
    rating: float = Field(description="Average brand rating")
    review_count: int = Field(description="Number of reviews")
    social_media: Dict[str, str] = Field(default_factory=dict, description="Social media links")
    created_at: datetime = Field(description="Creation time")
    updated_at: datetime = Field(description="Last update time")
    
    # Computed fields
    display_name: str = Field(description="Display name for the brand")
    is_established: bool = Field(description="Whether brand is well established")
    age: Optional[int] = Field(None, description="Brand age in years")
    social_links: List[Dict[str, str]] = Field(default_factory=list, description="Formatted social media links")
    rating_display: str = Field(description="Formatted rating display")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Apple",
                "slug": "apple",
                "description": "Technology company known for innovative products",
                "website": "https://www.apple.com",
                "email": "contact@apple.com",
                "phone": "+1-800-275-2273",
                "logo_url": "https://example.com/apple-logo.png",
                "company_name": "Apple Inc.",
                "founded_year": 1976,
                "country": "United States",
                "product_count": 250,
                "view_count": 15000,
                "rating": 4.5,
                "review_count": 1250,
                "display_name": "Apple",
                "is_established": True,
                "age": 48,
                "rating_display": "4.5/5.0 (1,250 reviews)",
                "is_active": True,
                "is_featured": True,
                "is_verified": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class BrandSummary(BaseModel):
    """Schema for brand summary in listings."""
    
    id: str = Field(description="Brand ID")
    name: str = Field(description="Brand name")
    slug: str = Field(description="Brand slug")
    logo_url: Optional[str] = Field(None, description="Brand logo URL")
    product_count: int = Field(description="Number of products from this brand")
    rating: float = Field(description="Average brand rating")
    is_featured: bool = Field(description="Whether brand is featured")
    is_verified: bool = Field(description="Whether brand is verified")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Apple",
                "slug": "apple",
                "logo_url": "https://example.com/apple-logo.png",
                "product_count": 250,
                "rating": 4.5,
                "is_featured": True,
                "is_verified": True
            }
        }


class BrandStats(BaseModel):
    """Schema for brand statistics."""
    
    id: str = Field(description="Brand ID")
    name: str = Field(description="Brand name")
    product_count: int = Field(description="Number of products")
    active_product_count: int = Field(description="Number of active products")
    view_count: int = Field(description="Number of views")
    rating: float = Field(description="Average brand rating")
    review_count: int = Field(description="Number of reviews")
    avg_product_price: Optional[float] = Field(None, description="Average product price")
    min_product_price: Optional[float] = Field(None, description="Minimum product price")
    max_product_price: Optional[float] = Field(None, description="Maximum product price")
    total_revenue: Optional[float] = Field(None, description="Total revenue from brand")
    market_share: Optional[float] = Field(None, description="Market share percentage")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Apple",
                "product_count": 250,
                "active_product_count": 245,
                "view_count": 15000,
                "rating": 4.5,
                "review_count": 1250,
                "avg_product_price": 899.99,
                "min_product_price": 99.99,
                "max_product_price": 2999.99,
                "total_revenue": 224997.50,
                "market_share": 15.5
            }
        }


class BrandBulkOperation(BaseModel):
    """Schema for bulk brand operations."""
    
    brand_ids: List[str] = Field(description="List of brand IDs")
    operation: str = Field(description="Operation type (activate, deactivate, delete, feature, unfeature, verify, unverify)")
    
    @validator("operation")
    def validate_operation(cls, v):
        """Validate operation type."""
        allowed_operations = ["activate", "deactivate", "delete", "feature", "unfeature", "verify", "unverify"]
        if v not in allowed_operations:
            raise ValueError(f"Operation must be one of: {', '.join(allowed_operations)}")
        return v
    
    @validator("brand_ids")
    def validate_brand_ids(cls, v):
        """Validate brand IDs list."""
        if not v:
            raise ValueError("At least one brand ID is required")
        if len(v) > 100:
            raise ValueError("Maximum 100 brands allowed per operation")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "brand_ids": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "456e7890-e89b-12d3-a456-426614174001"
                ],
                "operation": "feature"
            }
        }


class BrandImport(BaseModel):
    """Schema for brand import."""
    
    name: str = Field(description="Brand name")
    description: Optional[str] = Field(None, description="Brand description")
    website: Optional[str] = Field(None, description="Brand website URL")
    email: Optional[str] = Field(None, description="Brand contact email")
    phone: Optional[str] = Field(None, description="Brand contact phone")
    company_name: Optional[str] = Field(None, description="Company name")
    founded_year: Optional[int] = Field(None, description="Year company was founded")
    country: Optional[str] = Field(None, description="Country of origin")
    is_active: bool = Field(True, description="Whether brand is active")
    is_featured: bool = Field(False, description="Whether brand is featured")
    is_verified: bool = Field(False, description="Whether brand is verified")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Samsung",
                "description": "South Korean multinational electronics company",
                "website": "https://www.samsung.com",
                "email": "contact@samsung.com",
                "company_name": "Samsung Electronics Co., Ltd.",
                "founded_year": 1969,
                "country": "South Korea",
                "is_active": True,
                "is_featured": True,
                "is_verified": True
            }
        }


class BrandComparison(BaseModel):
    """Schema for brand comparison."""
    
    brands: List[BrandStats] = Field(description="List of brands to compare")
    comparison_metrics: Dict[str, Dict[str, float]] = Field(description="Comparison metrics")
    
    class Config:
        schema_extra = {
            "example": {
                "brands": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Apple",
                        "product_count": 250,
                        "rating": 4.5,
                        "market_share": 15.5
                    },
                    {
                        "id": "456e7890-e89b-12d3-a456-426614174001",
                        "name": "Samsung",
                        "product_count": 300,
                        "rating": 4.3,
                        "market_share": 18.2
                    }
                ],
                "comparison_metrics": {
                    "product_count": {"Apple": 250, "Samsung": 300},
                    "rating": {"Apple": 4.5, "Samsung": 4.3},
                    "market_share": {"Apple": 15.5, "Samsung": 18.2}
                }
            }
        }