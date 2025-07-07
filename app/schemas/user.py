"""User Pydantic schemas for authentication and user management.

This module contains all Pydantic models for user-related operations
including registration, login, profile management, and responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator

from app.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    email: EmailStr = Field(description="User email address")
    username: str = Field(min_length=3, max_length=50, description="Username")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    timezone: Optional[str] = Field("UTC", description="User timezone")
    language: Optional[str] = Field("en", description="User language")
    
    @validator("username")
    def validate_username(cls, v):
        """Validate username format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username can only contain letters, numbers, hyphens, and underscores")
        return v.lower()
    
    @validator("phone")
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v and not v.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "").isdigit():
            raise ValueError("Invalid phone number format")
        return v


class UserCreate(UserBase):
    """Schema for user registration."""
    
    password: str = Field(min_length=8, description="User password")
    confirm_password: str = Field(description="Password confirmation")
    role: Optional[UserRole] = Field(UserRole.BUYER, description="User role")
    
    @validator("password")
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, one digit, and one special character"
            )
        
        return v
    
    @validator("confirm_password")
    def validate_password_match(cls, v, values):
        """Validate password confirmation."""
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "role": "buyer"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login."""
    
    email: EmailStr = Field(description="User email address")
    password: str = Field(description="User password")
    remember_me: bool = Field(False, description="Remember login")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "remember_me": False
            }
        }


class UserUpdate(BaseModel):
    """Schema for user profile updates."""
    
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    timezone: Optional[str] = Field(None, description="User timezone")
    language: Optional[str] = Field(None, description="User language")
    
    @validator("phone")
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v and not v.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "").isdigit():
            raise ValueError("Invalid phone number format")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "bio": "Software developer passionate about e-commerce",
                "timezone": "America/New_York",
                "language": "en"
            }
        }


class UserPasswordChange(BaseModel):
    """Schema for password change."""
    
    current_password: str = Field(description="Current password")
    new_password: str = Field(min_length=8, description="New password")
    confirm_password: str = Field(description="Password confirmation")
    
    @validator("new_password")
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, one digit, and one special character"
            )
        
        return v
    
    @validator("confirm_password")
    def validate_password_match(cls, v, values):
        """Validate password confirmation."""
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Passwords do not match")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "OldPass123!",
                "new_password": "NewSecurePass123!",
                "confirm_password": "NewSecurePass123!"
            }
        }


class UserPasswordReset(BaseModel):
    """Schema for password reset request."""
    
    email: EmailStr = Field(description="User email address")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class UserPasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    
    token: str = Field(description="Reset token")
    new_password: str = Field(min_length=8, description="New password")
    confirm_password: str = Field(description="Password confirmation")
    
    @validator("new_password")
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, one digit, and one special character"
            )
        
        return v
    
    @validator("confirm_password")
    def validate_password_match(cls, v, values):
        """Validate password confirmation."""
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Passwords do not match")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "token": "reset-token-123",
                "new_password": "NewSecurePass123!",
                "confirm_password": "NewSecurePass123!"
            }
        }


class User(UserBase):
    """Schema for user response."""
    
    id: str = Field(description="User ID")
    role: UserRole = Field(description="User role")
    status: UserStatus = Field(description="User status")
    is_active: bool = Field(description="Whether user is active")
    is_verified: bool = Field(description="Whether email is verified")
    is_superuser: bool = Field(description="Whether user is superuser")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    last_login: Optional[datetime] = Field(None, description="Last login time")
    login_count: int = Field(description="Total login count")
    created_at: datetime = Field(description="Account creation time")
    updated_at: datetime = Field(description="Last update time")
    
    # Computed fields
    full_name: str = Field(description="Full name")
    is_admin: bool = Field(description="Whether user has admin privileges")
    is_seller: bool = Field(description="Whether user has seller privileges")
    is_buyer: bool = Field(description="Whether user has buyer privileges")
    can_login: bool = Field(description="Whether user can login")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "role": "buyer",
                "status": "active",
                "is_active": True,
                "is_verified": True,
                "is_superuser": False,
                "full_name": "John Doe",
                "is_admin": False,
                "is_seller": False,
                "is_buyer": True,
                "can_login": True,
                "login_count": 5,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class UserResponse(BaseModel):
    """Schema for user response with token."""
    
    user: User = Field(description="User information")
    access_token: Optional[str] = Field(None, description="Access token")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "username": "johndoe",
                    "full_name": "John Doe",
                    "role": "buyer"
                },
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class UserSummary(BaseModel):
    """Schema for user summary in listings."""
    
    id: str = Field(description="User ID")
    username: str = Field(description="Username")
    full_name: str = Field(description="Full name")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    role: UserRole = Field(description="User role")
    is_verified: bool = Field(description="Whether email is verified")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "johndoe",
                "full_name": "John Doe",
                "avatar_url": "https://example.com/avatar.jpg",
                "role": "buyer",
                "is_verified": True
            }
        }


class TokenResponse(BaseModel):
    """Schema for token response."""
    
    access_token: str = Field(description="Access token")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(description="Token expiration in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    
    refresh_token: str = Field(description="Refresh token")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }