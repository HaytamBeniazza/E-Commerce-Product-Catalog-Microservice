"""Base model class for all database models.

This module provides the base model class with common fields and functionality
that all other models inherit from, including timestamps, UUID primary keys,
and common utility methods.
"""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models.
    
    Provides common functionality including:
    - UUID primary key
    - Created and updated timestamps
    - Utility methods for serialization
    """
    
    # Abstract base class - no table will be created
    __abstract__ = True
    
    # Primary key as UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Timestamp fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True
    )
    
    def to_dict(self, exclude_fields: set = None) -> Dict[str, Any]:
        """Convert model instance to dictionary.
        
        Args:
            exclude_fields: Set of field names to exclude from the result
            
        Returns:
            Dictionary representation of the model
        """
        exclude_fields = exclude_fields or set()
        
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)
                
                # Handle special types
                if isinstance(value, uuid.UUID):
                    result[column.name] = str(value)
                elif isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                else:
                    result[column.name] = value
        
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude_fields: set = None) -> None:
        """Update model instance from dictionary.
        
        Args:
            data: Dictionary with field values to update
            exclude_fields: Set of field names to exclude from update
        """
        exclude_fields = exclude_fields or {'id', 'created_at'}
        
        for key, value in data.items():
            if key not in exclude_fields and hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def get_column_names(cls) -> list[str]:
        """Get list of column names for the model.
        
        Returns:
            List of column names
        """
        return [column.name for column in cls.__table__.columns]
    
    @classmethod
    def get_searchable_fields(cls) -> list[str]:
        """Get list of searchable fields for the model.
        
        This method should be overridden in child classes to specify
        which fields are searchable.
        
        Returns:
            List of searchable field names
        """
        return []
    
    def __repr__(self) -> str:
        """String representation of the model.
        
        Returns:
            String representation
        """
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def __str__(self) -> str:
        """Human-readable string representation.
        
        Returns:
            String representation
        """
        return self.__repr__()