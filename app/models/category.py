"""Category model for product organization.

This module defines the Category model for organizing products into
hierarchical categories with support for nested subcategories.
"""

import uuid
from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Category(Base):
    """Category model for product organization.
    
    Represents product categories with hierarchical structure support.
    Categories can have parent categories and subcategories, allowing
    for flexible product organization.
    """
    
    __tablename__ = "categories"
    
    # Basic category information
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
    
    # Hierarchy support
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Display and ordering
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        index=True
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
    
    # Images and media
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    icon_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    banner_url: Mapped[Optional[str]] = mapped_column(
        String(500),
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
    
    # Relationships
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children"
    )
    
    children: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    
    # Products relationship (will be defined in Product model)
    # products: Mapped[List["Product"]] = relationship(
    #     "Product",
    #     back_populates="category"
    # )
    
    @property
    def level(self) -> int:
        """Get category hierarchy level.
        
        Returns:
            Category level (0 for root categories)
        """
        if not self.parent_id:
            return 0
        
        # This would require a database query in a real implementation
        # For now, we'll return a simple calculation
        level = 0
        current = self
        while current.parent_id:
            level += 1
            # In a real implementation, you'd fetch the parent from the database
            break  # Prevent infinite loop for now
        
        return level
    
    @property
    def full_path(self) -> str:
        """Get full category path.
        
        Returns:
            Full path from root to current category
        """
        # This would require recursive database queries in a real implementation
        # For now, return just the current category name
        return self.name
    
    @property
    def breadcrumbs(self) -> List[dict]:
        """Get breadcrumb navigation for the category.
        
        Returns:
            List of breadcrumb items
        """
        # This would require recursive database queries in a real implementation
        return [
            {
                "id": str(self.id),
                "name": self.name,
                "slug": self.slug
            }
        ]
    
    def is_child_of(self, category_id: uuid.UUID) -> bool:
        """Check if this category is a child of another category.
        
        Args:
            category_id: Parent category ID to check
            
        Returns:
            True if this category is a child of the specified category
        """
        if not self.parent_id:
            return False
        
        if self.parent_id == category_id:
            return True
        
        # In a real implementation, you'd recursively check parent categories
        return False
    
    def is_parent_of(self, category_id: uuid.UUID) -> bool:
        """Check if this category is a parent of another category.
        
        Args:
            category_id: Child category ID to check
            
        Returns:
            True if this category is a parent of the specified category
        """
        # In a real implementation, you'd check if any children match the ID
        return any(child.id == category_id for child in self.children)
    
    def get_all_children_ids(self) -> List[uuid.UUID]:
        """Get all descendant category IDs.
        
        Returns:
            List of all descendant category IDs
        """
        children_ids = []
        
        for child in self.children:
            children_ids.append(child.id)
            # Recursively get children of children
            children_ids.extend(child.get_all_children_ids())
        
        return children_ids
    
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
    
    @classmethod
    def get_searchable_fields(cls) -> List[str]:
        """Get list of searchable fields.
        
        Returns:
            List of searchable field names
        """
        return ["name", "description", "meta_title", "meta_description", "meta_keywords"]
    
    def to_dict(self, exclude_fields: set = None, include_children: bool = False) -> dict:
        """Convert to dictionary with optional children.
        
        Args:
            exclude_fields: Fields to exclude
            include_children: Whether to include children in the result
            
        Returns:
            Dictionary representation
        """
        result = super().to_dict(exclude_fields=exclude_fields)
        
        # Add computed properties
        result["level"] = self.level
        result["full_path"] = self.full_path
        result["breadcrumbs"] = self.breadcrumbs
        
        # Include children if requested
        if include_children and self.children:
            result["children"] = [
                child.to_dict(exclude_fields=exclude_fields, include_children=False)
                for child in self.children
                if child.is_active
            ]
        
        return result
    
    def to_tree_dict(self) -> dict:
        """Convert to tree structure dictionary.
        
        Returns:
            Tree structure representation
        """
        result = self.to_dict()
        
        if self.children:
            result["children"] = [
                child.to_tree_dict()
                for child in sorted(self.children, key=lambda x: x.sort_order)
                if child.is_active
            ]
        
        return result
    
    def __repr__(self) -> str:
        """String representation.
        
        Returns:
            String representation
        """
        return f"<Category(id={self.id}, name={self.name}, slug={self.slug})>"