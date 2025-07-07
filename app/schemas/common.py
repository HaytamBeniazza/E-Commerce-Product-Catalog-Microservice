"""Common Pydantic schemas for shared functionality.

This module contains common schemas used across the application
including pagination, search parameters, and standard responses.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, validator

# Generic type for paginated responses
T = TypeVar("T")


class SuccessResponse(BaseModel):
    """Standard success response schema."""
    
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {"id": "123e4567-e89b-12d3-a456-426614174000"}
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "details": {"field": "name", "issue": "This field is required"}
            }
        }


class PaginationParams(BaseModel):
    """Pagination parameters schema."""
    
    page: int = Field(1, ge=1, description="Page number (1-based)")
    size: int = Field(20, ge=1, le=100, description="Page size")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.size
    
    @property
    def limit(self) -> int:
        """Get limit for database queries."""
        return self.size
    
    class Config:
        schema_extra = {
            "example": {
                "page": 1,
                "size": 20
            }
        }


class PaginationMeta(BaseModel):
    """Pagination metadata schema."""
    
    page: int = Field(description="Current page number")
    size: int = Field(description="Page size")
    total: int = Field(description="Total number of items")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")
    
    class Config:
        schema_extra = {
            "example": {
                "page": 1,
                "size": 20,
                "total": 150,
                "pages": 8,
                "has_next": True,
                "has_prev": False
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema."""
    
    items: List[T] = Field(description="List of items")
    meta: PaginationMeta = Field(description="Pagination metadata")
    
    @classmethod
    def create(
        cls,
        items: List[T],
        page: int,
        size: int,
        total: int
    ) -> "PaginatedResponse[T]":
        """Create paginated response with calculated metadata.
        
        Args:
            items: List of items
            page: Current page number
            size: Page size
            total: Total number of items
            
        Returns:
            PaginatedResponse instance
        """
        pages = (total + size - 1) // size  # Ceiling division
        
        meta = PaginationMeta(
            page=page,
            size=size,
            total=total,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )
        
        return cls(items=items, meta=meta)


class SearchParams(BaseModel):
    """Search parameters schema."""
    
    q: Optional[str] = Field(None, description="Search query")
    category_id: Optional[str] = Field(None, description="Category filter")
    brand_id: Optional[str] = Field(None, description="Brand filter")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    in_stock: Optional[bool] = Field(None, description="Stock availability filter")
    is_featured: Optional[bool] = Field(None, description="Featured products filter")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")
    
    @validator("sort_order")
    def validate_sort_order(cls, v):
        """Validate sort order."""
        if v.lower() not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v.lower()
    
    @validator("sort_by")
    def validate_sort_by(cls, v):
        """Validate sort field."""
        valid_fields = [
            "created_at", "updated_at", "name", "price", 
            "rating", "review_count", "stock_quantity", "sales_count"
        ]
        if v not in valid_fields:
            raise ValueError(f"Sort field must be one of: {', '.join(valid_fields)}")
        return v
    
    @validator("max_price")
    def validate_price_range(cls, v, values):
        """Validate price range."""
        if v is not None and "min_price" in values and values["min_price"] is not None:
            if v < values["min_price"]:
                raise ValueError("Maximum price must be greater than minimum price")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "q": "laptop",
                "category_id": "123e4567-e89b-12d3-a456-426614174000",
                "min_price": 100.0,
                "max_price": 1000.0,
                "in_stock": True,
                "sort_by": "price",
                "sort_order": "asc"
            }
        }


class FilterParams(BaseModel):
    """Advanced filter parameters schema."""
    
    categories: Optional[List[str]] = Field(None, description="Category IDs")
    brands: Optional[List[str]] = Field(None, description="Brand IDs")
    price_ranges: Optional[List[str]] = Field(None, description="Price ranges")
    ratings: Optional[List[int]] = Field(None, description="Rating filters")
    attributes: Optional[Dict[str, List[str]]] = Field(None, description="Product attributes")
    
    @validator("ratings")
    def validate_ratings(cls, v):
        """Validate rating values."""
        if v:
            for rating in v:
                if rating < 1 or rating > 5:
                    raise ValueError("Rating must be between 1 and 5")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "categories": ["123e4567-e89b-12d3-a456-426614174000"],
                "brands": ["456e7890-e89b-12d3-a456-426614174000"],
                "price_ranges": ["100-500", "500-1000"],
                "ratings": [4, 5],
                "attributes": {
                    "color": ["red", "blue"],
                    "size": ["M", "L"]
                }
            }
        }


class SortParams(BaseModel):
    """Sort parameters schema."""
    
    field: str = Field("created_at", description="Sort field")
    order: str = Field("desc", description="Sort order")
    
    @validator("order")
    def validate_order(cls, v):
        """Validate sort order."""
        if v.lower() not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v.lower()
    
    class Config:
        schema_extra = {
            "example": {
                "field": "price",
                "order": "asc"
            }
        }


class HealthCheck(BaseModel):
    """Health check response schema."""
    
    status: str = Field(description="Service status")
    service: str = Field(description="Service name")
    version: str = Field(description="Service version")
    environment: str = Field(description="Environment")
    timestamp: float = Field(description="Timestamp")
    dependencies: Optional[Dict[str, bool]] = Field(None, description="Dependency status")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "service": "E-Commerce Product Catalog",
                "version": "1.0.0",
                "environment": "development",
                "timestamp": 1640995200.0,
                "dependencies": {
                    "database": True,
                    "cache": True
                }
            }
        }


class BulkOperation(BaseModel):
    """Bulk operation request schema."""
    
    operation: str = Field(description="Operation type")
    items: List[Dict[str, Any]] = Field(description="Items to process")
    options: Optional[Dict[str, Any]] = Field(None, description="Operation options")
    
    @validator("operation")
    def validate_operation(cls, v):
        """Validate operation type."""
        valid_operations = ["create", "update", "delete", "import", "export"]
        if v not in valid_operations:
            raise ValueError(f"Operation must be one of: {', '.join(valid_operations)}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "operation": "create",
                "items": [
                    {"name": "Product 1", "price": 100.0},
                    {"name": "Product 2", "price": 200.0}
                ],
                "options": {
                    "validate_only": False,
                    "skip_duplicates": True
                }
            }
        }


class BulkOperationResult(BaseModel):
    """Bulk operation result schema."""
    
    operation: str = Field(description="Operation type")
    total: int = Field(description="Total items processed")
    successful: int = Field(description="Successfully processed items")
    failed: int = Field(description="Failed items")
    errors: List[Dict[str, Any]] = Field(description="Error details")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="Operation results")
    
    class Config:
        schema_extra = {
            "example": {
                "operation": "create",
                "total": 2,
                "successful": 1,
                "failed": 1,
                "errors": [
                    {
                        "item_index": 1,
                        "error": "Duplicate SKU",
                        "details": {"sku": "PROD-001"}
                    }
                ],
                "results": [
                    {"id": "123e4567-e89b-12d3-a456-426614174000", "status": "created"}
                ]
            }
        }