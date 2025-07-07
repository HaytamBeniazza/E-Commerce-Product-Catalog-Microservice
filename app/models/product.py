"""Product models for the e-commerce catalog.

This module defines the Product and ProductImage models for managing
product information, inventory, pricing, and associated images.
"""

import uuid
from decimal import Decimal
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ProductStatus(str, PyEnum):
    """Product status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"
    OUT_OF_STOCK = "out_of_stock"


class ProductType(str, PyEnum):
    """Product type enumeration."""
    SIMPLE = "simple"
    VARIABLE = "variable"
    GROUPED = "grouped"
    EXTERNAL = "external"
    DIGITAL = "digital"


class Product(Base):
    """Product model for e-commerce catalog.
    
    Represents products in the catalog with comprehensive information
    including pricing, inventory, categories, brands, and metadata.
    """
    
    __tablename__ = "products"
    
    # Basic product information
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    
    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    short_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Product identification
    sku: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    
    barcode: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    
    # Pricing
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        index=True
    )
    
    compare_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    
    cost_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    
    # Inventory management
    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        index=True
    )
    
    min_stock_level: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False
    )
    
    max_stock_level: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    
    track_inventory: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    
    allow_backorder: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # Product relationships
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    brand_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Product attributes
    weight: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 3),
        nullable=True
    )
    
    dimensions_length: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 2),
        nullable=True
    )
    
    dimensions_width: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 2),
        nullable=True
    )
    
    dimensions_height: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 2),
        nullable=True
    )
    
    # Status and visibility
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus),
        default=ProductStatus.DRAFT,
        nullable=False,
        index=True
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    is_digital: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    requires_shipping: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    
    # SEO and metadata
    meta_title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    meta_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    meta_keywords: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Analytics and metrics
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    rating: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        default=0,
        nullable=False
    )
    
    review_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    sales_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    # Relationships
    category: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="products"
    )
    
    brand: Mapped[Optional["Brand"]] = relationship(
        "Brand",
        back_populates="products"
    )
    
    images: Mapped[List["ProductImage"]] = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.sort_order"
    )
    
    # Properties
    @property
    def is_in_stock(self) -> bool:
        """Check if product is in stock.
        
        Returns:
            True if product is in stock
        """
        if not self.track_inventory:
            return True
        return self.stock_quantity > 0 or self.allow_backorder
    
    @property
    def is_low_stock(self) -> bool:
        """Check if product is low in stock.
        
        Returns:
            True if product stock is below minimum level
        """
        if not self.track_inventory:
            return False
        return self.stock_quantity <= self.min_stock_level
    
    @property
    def is_out_of_stock(self) -> bool:
        """Check if product is out of stock.
        
        Returns:
            True if product is out of stock
        """
        if not self.track_inventory:
            return False
        return self.stock_quantity <= 0
    
    @property
    def discount_percentage(self) -> Optional[float]:
        """Calculate discount percentage if compare price is set.
        
        Returns:
            Discount percentage or None
        """
        if not self.compare_price or self.compare_price <= self.price:
            return None
        
        discount = (self.compare_price - self.price) / self.compare_price * 100
        return round(float(discount), 2)
    
    @property
    def profit_margin(self) -> Optional[float]:
        """Calculate profit margin if cost price is set.
        
        Returns:
            Profit margin percentage or None
        """
        if not self.cost_price or self.cost_price <= 0:
            return None
        
        margin = (self.price - self.cost_price) / self.price * 100
        return round(float(margin), 2)
    
    @property
    def primary_image(self) -> Optional["ProductImage"]:
        """Get primary product image.
        
        Returns:
            Primary image or first image if no primary is set
        """
        # Find primary image
        for image in self.images:
            if image.is_primary:
                return image
        
        # Return first image if no primary is set
        return self.images[0] if self.images else None
    
    @property
    def dimensions(self) -> Optional[dict]:
        """Get product dimensions as dictionary.
        
        Returns:
            Dimensions dictionary or None
        """
        if not any([self.dimensions_length, self.dimensions_width, self.dimensions_height]):
            return None
        
        return {
            "length": float(self.dimensions_length) if self.dimensions_length else None,
            "width": float(self.dimensions_width) if self.dimensions_width else None,
            "height": float(self.dimensions_height) if self.dimensions_height else None,
            "weight": float(self.weight) if self.weight else None
        }
    
    @property
    def rating_display(self) -> str:
        """Get formatted rating display.
        
        Returns:
            Formatted rating string
        """
        if self.review_count == 0:
            return "No ratings"
        
        return f"{float(self.rating):.1f} ({self.review_count} reviews)"
    
    # Methods
    def increment_view_count(self) -> None:
        """Increment product view count."""
        self.view_count += 1
    
    def increment_sales_count(self, quantity: int = 1) -> None:
        """Increment sales count.
        
        Args:
            quantity: Quantity sold
        """
        self.sales_count += quantity
    
    def update_stock(self, quantity: int) -> bool:
        """Update stock quantity.
        
        Args:
            quantity: New stock quantity
            
        Returns:
            True if update was successful
        """
        if not self.track_inventory:
            return True
        
        if quantity < 0:
            return False
        
        self.stock_quantity = quantity
        
        # Update status based on stock
        if quantity == 0 and not self.allow_backorder:
            self.status = ProductStatus.OUT_OF_STOCK
        elif self.status == ProductStatus.OUT_OF_STOCK and quantity > 0:
            self.status = ProductStatus.ACTIVE
        
        return True
    
    def reduce_stock(self, quantity: int) -> bool:
        """Reduce stock quantity.
        
        Args:
            quantity: Quantity to reduce
            
        Returns:
            True if reduction was successful
        """
        if not self.track_inventory:
            return True
        
        if quantity <= 0:
            return False
        
        if self.stock_quantity < quantity and not self.allow_backorder:
            return False
        
        self.stock_quantity -= quantity
        
        # Update status if out of stock
        if self.stock_quantity <= 0 and not self.allow_backorder:
            self.status = ProductStatus.OUT_OF_STOCK
        
        return True
    
    def increase_stock(self, quantity: int) -> bool:
        """Increase stock quantity.
        
        Args:
            quantity: Quantity to add
            
        Returns:
            True if increase was successful
        """
        if quantity <= 0:
            return False
        
        self.stock_quantity += quantity
        
        # Update status if was out of stock
        if self.status == ProductStatus.OUT_OF_STOCK:
            self.status = ProductStatus.ACTIVE
        
        return True
    
    def update_rating(self, new_rating: float, review_count: int) -> None:
        """Update product rating.
        
        Args:
            new_rating: New average rating
            review_count: Total number of reviews
        """
        self.rating = Decimal(str(round(new_rating, 2)))
        self.review_count = review_count
    
    def set_primary_image(self, image_id: uuid.UUID) -> bool:
        """Set primary image.
        
        Args:
            image_id: Image ID to set as primary
            
        Returns:
            True if image was found and set as primary
        """
        # Remove primary flag from all images
        for image in self.images:
            image.is_primary = False
        
        # Set new primary image
        for image in self.images:
            if image.id == image_id:
                image.is_primary = True
                return True
        
        return False
    
    @classmethod
    def get_searchable_fields(cls) -> list[str]:
        """Get list of searchable fields.
        
        Returns:
            List of searchable field names
        """
        return [
            "name", "description", "short_description", "sku", "barcode",
            "meta_title", "meta_description", "meta_keywords"
        ]
    
    def to_dict(self, exclude_fields: set = None, include_images: bool = True) -> dict:
        """Convert to dictionary with optional images.
        
        Args:
            exclude_fields: Fields to exclude
            include_images: Whether to include images
            
        Returns:
            Dictionary representation
        """
        result = super().to_dict(exclude_fields=exclude_fields)
        
        # Convert Decimal fields to float for JSON serialization
        decimal_fields = ['price', 'compare_price', 'cost_price', 'weight', 
                         'dimensions_length', 'dimensions_width', 'dimensions_height', 'rating']
        
        for field in decimal_fields:
            if field in result and result[field] is not None:
                result[field] = float(result[field])
        
        # Add computed properties
        result["is_in_stock"] = self.is_in_stock
        result["is_low_stock"] = self.is_low_stock
        result["is_out_of_stock"] = self.is_out_of_stock
        result["discount_percentage"] = self.discount_percentage
        result["profit_margin"] = self.profit_margin
        result["dimensions"] = self.dimensions
        result["rating_display"] = self.rating_display
        
        # Include category and brand info
        if self.category:
            result["category"] = {
                "id": str(self.category.id),
                "name": self.category.name,
                "slug": self.category.slug
            }
        
        if self.brand:
            result["brand"] = {
                "id": str(self.brand.id),
                "name": self.brand.name,
                "slug": self.brand.slug,
                "logo_url": self.brand.logo_url
            }
        
        # Include images if requested
        if include_images and self.images:
            result["images"] = [image.to_dict() for image in self.images]
            
            # Add primary image separately
            primary_img = self.primary_image
            result["primary_image"] = primary_img.to_dict() if primary_img else None
        
        return result
    
    def to_summary_dict(self) -> dict:
        """Convert to summary dictionary for listings.
        
        Returns:
            Summary dictionary representation
        """
        primary_img = self.primary_image
        
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "price": float(self.price),
            "compare_price": float(self.compare_price) if self.compare_price else None,
            "discount_percentage": self.discount_percentage,
            "rating": float(self.rating),
            "review_count": self.review_count,
            "is_in_stock": self.is_in_stock,
            "is_featured": self.is_featured,
            "primary_image_url": primary_img.image_url if primary_img else None,
            "category_name": self.category.name if self.category else None,
            "brand_name": self.brand.name if self.brand else None
        }
    
    def __repr__(self) -> str:
        """String representation.
        
        Returns:
            String representation
        """
        return f"<Product(id={self.id}, name={self.name}, sku={self.sku})>"


class ProductImage(Base):
    """Product image model for managing product photos.
    
    Represents images associated with products including URLs,
    alt text, and ordering information.
    """
    
    __tablename__ = "product_images"
    
    # Product relationship
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Image information
    image_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    
    alt_text: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    # Image metadata
    filename: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    
    width: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    
    height: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    
    # Display settings
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        index=True
    )
    
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    # Relationships
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="images"
    )
    
    @property
    def aspect_ratio(self) -> Optional[float]:
        """Calculate image aspect ratio.
        
        Returns:
            Aspect ratio or None if dimensions are not available
        """
        if not self.width or not self.height:
            return None
        
        return round(self.width / self.height, 2)
    
    @property
    def file_size_mb(self) -> Optional[float]:
        """Get file size in megabytes.
        
        Returns:
            File size in MB or None
        """
        if not self.file_size:
            return None
        
        return round(self.file_size / (1024 * 1024), 2)
    
    def to_dict(self, exclude_fields: set = None) -> dict:
        """Convert to dictionary.
        
        Args:
            exclude_fields: Fields to exclude
            
        Returns:
            Dictionary representation
        """
        result = super().to_dict(exclude_fields=exclude_fields)
        
        # Add computed properties
        result["aspect_ratio"] = self.aspect_ratio
        result["file_size_mb"] = self.file_size_mb
        
        return result
    
    def __repr__(self) -> str:
        """String representation.
        
        Returns:
            String representation
        """
        return f"<ProductImage(id={self.id}, product_id={self.product_id}, is_primary={self.is_primary})>"