"""Brand model for product brand management.

This module defines the Brand model for managing product brands
with support for brand information, logos, and metadata.
"""

from typing import Optional

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Brand(Base):
    """Brand model for product brand management.
    
    Represents product brands with information, logos, and metadata.
    Brands can be associated with multiple products and provide
    brand-specific information and filtering capabilities.
    """
    
    __tablename__ = "brands"
    
    # Basic brand information
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Brand details
    website_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    
    # Company information
    company_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True
    )
    
    founded_year: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    
    country: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    # Brand media
    logo_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    banner_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
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
    
    # Status and visibility
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
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # Display and ordering
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        index=True
    )
    
    # Analytics and metrics
    product_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    rating: Mapped[float] = mapped_column(
        default=0.0,
        nullable=False
    )
    
    review_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    # Social media links
    facebook_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    twitter_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    instagram_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    linkedin_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    # Relationships
    # Products relationship (will be defined in Product model)
    # products: Mapped[List["Product"]] = relationship(
    #     "Product",
    #     back_populates="brand"
    # )
    
    def increment_product_count(self, amount: int = 1) -> None:
        """Increment product count.
        
        Args:
            amount: Amount to increment by
        """
        self.product_count += amount
    
    def decrement_product_count(self, amount: int = 1) -> None:
        """Decrement product count.
        
        Args:
            amount: Amount to decrement by
        """
        self.product_count = max(0, self.product_count - amount)
    
    def increment_view_count(self) -> None:
        """Increment view count for analytics."""
        self.view_count += 1
    
    def update_rating(self, new_rating: float, review_count: int) -> None:
        """Update brand rating based on product reviews.
        
        Args:
            new_rating: New average rating
            review_count: Total number of reviews
        """
        self.rating = round(new_rating, 2)
        self.review_count = review_count
    
    @property
    def display_name(self) -> str:
        """Get display name for the brand.
        
        Returns:
            Brand display name
        """
        return self.name
    
    @property
    def is_established(self) -> bool:
        """Check if brand is established (has founding year).
        
        Returns:
            True if brand has founding year
        """
        return self.founded_year is not None
    
    @property
    def age_years(self) -> Optional[int]:
        """Get brand age in years.
        
        Returns:
            Brand age in years or None if founding year is not set
        """
        if not self.founded_year:
            return None
        
        from datetime import datetime
        current_year = datetime.now().year
        return current_year - self.founded_year
    
    @property
    def social_media_links(self) -> dict:
        """Get all social media links.
        
        Returns:
            Dictionary of social media links
        """
        links = {}
        
        if self.facebook_url:
            links["facebook"] = self.facebook_url
        if self.twitter_url:
            links["twitter"] = self.twitter_url
        if self.instagram_url:
            links["instagram"] = self.instagram_url
        if self.linkedin_url:
            links["linkedin"] = self.linkedin_url
        
        return links
    
    @property
    def has_social_media(self) -> bool:
        """Check if brand has any social media links.
        
        Returns:
            True if brand has social media links
        """
        return bool(self.social_media_links)
    
    @property
    def rating_display(self) -> str:
        """Get formatted rating display.
        
        Returns:
            Formatted rating string
        """
        if self.review_count == 0:
            return "No ratings"
        
        return f"{self.rating:.1f} ({self.review_count} reviews)"
    
    @classmethod
    def get_searchable_fields(cls) -> list[str]:
        """Get list of searchable fields.
        
        Returns:
            List of searchable field names
        """
        return [
            "name", "description", "company_name", "country",
            "meta_title", "meta_description", "meta_keywords"
        ]
    
    def to_dict(self, exclude_fields: set = None, include_stats: bool = True) -> dict:
        """Convert to dictionary with optional statistics.
        
        Args:
            exclude_fields: Fields to exclude
            include_stats: Whether to include statistics
            
        Returns:
            Dictionary representation
        """
        result = super().to_dict(exclude_fields=exclude_fields)
        
        # Add computed properties
        result["display_name"] = self.display_name
        result["is_established"] = self.is_established
        result["age_years"] = self.age_years
        result["has_social_media"] = self.has_social_media
        result["rating_display"] = self.rating_display
        
        if include_stats:
            result["social_media_links"] = self.social_media_links
        
        return result
    
    def to_summary_dict(self) -> dict:
        """Convert to summary dictionary for listings.
        
        Returns:
            Summary dictionary representation
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "logo_url": self.logo_url,
            "is_verified": self.is_verified,
            "is_featured": self.is_featured,
            "product_count": self.product_count,
            "rating": self.rating,
            "review_count": self.review_count,
            "rating_display": self.rating_display
        }
    
    def __repr__(self) -> str:
        """String representation.
        
        Returns:
            String representation
        """
        return f"<Brand(id={self.id}, name={self.name}, slug={self.slug})>"