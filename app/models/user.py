"""User model for authentication and user management.

This module defines the User model with authentication fields,
role-based access control, and user profile information.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserRole(str, PyEnum):
    """User role enumeration."""
    ADMIN = "admin"
    SELLER = "seller"
    BUYER = "buyer"


class UserStatus(str, PyEnum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(Base):
    """User model for authentication and profile management.
    
    Represents users in the system with different roles and permissions.
    Supports authentication, authorization, and user profile management.
    """
    
    __tablename__ = "users"
    
    # Basic user information
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    # Profile information
    first_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    last_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Role and permissions
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.BUYER,
        nullable=False,
        index=True
    )
    
    # Status and flags
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus),
        default=UserStatus.PENDING,
        nullable=False,
        index=True
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # Authentication tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    login_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )
    
    failed_login_attempts: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )
    
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Email verification
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    verification_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    # Password reset
    password_reset_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    password_reset_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Preferences and settings
    timezone: Mapped[Optional[str]] = mapped_column(
        String(50),
        default="UTC",
        nullable=True
    )
    
    language: Mapped[Optional[str]] = mapped_column(
        String(10),
        default="en",
        nullable=True
    )
    
    # Relationships
    # Note: Product relationships will be added when Product model is created
    
    @property
    def full_name(self) -> str:
        """Get user's full name.
        
        Returns:
            Full name or username if names are not provided
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    @property
    def is_admin(self) -> bool:
        """Check if user is an admin.
        
        Returns:
            True if user is admin or superuser
        """
        return self.role == UserRole.ADMIN or self.is_superuser
    
    @property
    def is_seller(self) -> bool:
        """Check if user is a seller.
        
        Returns:
            True if user is seller, admin, or superuser
        """
        return self.role in [UserRole.SELLER, UserRole.ADMIN] or self.is_superuser
    
    @property
    def is_buyer(self) -> bool:
        """Check if user is a buyer.
        
        Returns:
            True if user has buyer role or higher
        """
        return self.role in [UserRole.BUYER, UserRole.SELLER, UserRole.ADMIN] or self.is_superuser
    
    @property
    def is_locked(self) -> bool:
        """Check if user account is locked.
        
        Returns:
            True if account is locked
        """
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False
    
    def can_login(self) -> bool:
        """Check if user can login.
        
        Returns:
            True if user can login
        """
        return (
            self.is_active and
            self.status == UserStatus.ACTIVE and
            not self.is_locked
        )
    
    def increment_login_count(self) -> None:
        """Increment login count and update last login time."""
        self.login_count += 1
        self.last_login = datetime.utcnow()
        self.failed_login_attempts = 0  # Reset failed attempts on successful login
    
    def increment_failed_login(self, max_attempts: int = 5, lockout_minutes: int = 15) -> None:
        """Increment failed login attempts and lock account if necessary.
        
        Args:
            max_attempts: Maximum allowed failed attempts
            lockout_minutes: Lockout duration in minutes
        """
        self.failed_login_attempts += 1
        
        if self.failed_login_attempts >= max_attempts:
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
    
    def unlock_account(self) -> None:
        """Unlock user account."""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def verify_email(self) -> None:
        """Mark email as verified."""
        self.is_verified = True
        self.email_verified_at = datetime.utcnow()
        self.verification_token = None
        
        # Activate account if it was pending verification
        if self.status == UserStatus.PENDING:
            self.status = UserStatus.ACTIVE
    
    def set_password_reset_token(self, token: str, expires_minutes: int = 60) -> None:
        """Set password reset token.
        
        Args:
            token: Reset token
            expires_minutes: Token expiration time in minutes
        """
        from datetime import timedelta
        
        self.password_reset_token = token
        self.password_reset_expires = datetime.utcnow() + timedelta(minutes=expires_minutes)
    
    def clear_password_reset_token(self) -> None:
        """Clear password reset token."""
        self.password_reset_token = None
        self.password_reset_expires = None
    
    def is_password_reset_token_valid(self) -> bool:
        """Check if password reset token is valid.
        
        Returns:
            True if token is valid and not expired
        """
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        
        return datetime.utcnow() < self.password_reset_expires
    
    @classmethod
    def get_searchable_fields(cls) -> list[str]:
        """Get list of searchable fields.
        
        Returns:
            List of searchable field names
        """
        return ["email", "username", "first_name", "last_name"]
    
    def to_dict(self, exclude_fields: set = None) -> dict:
        """Convert to dictionary, excluding sensitive fields by default.
        
        Args:
            exclude_fields: Additional fields to exclude
            
        Returns:
            Dictionary representation
        """
        default_exclude = {
            "hashed_password",
            "verification_token",
            "password_reset_token",
            "password_reset_expires"
        }
        
        if exclude_fields:
            default_exclude.update(exclude_fields)
        
        result = super().to_dict(exclude_fields=default_exclude)
        
        # Add computed properties
        result["full_name"] = self.full_name
        result["is_admin"] = self.is_admin
        result["is_seller"] = self.is_seller
        result["is_buyer"] = self.is_buyer
        result["is_locked"] = self.is_locked
        result["can_login"] = self.can_login()
        
        return result
    
    def __repr__(self) -> str:
        """String representation.
        
        Returns:
            String representation
        """
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"