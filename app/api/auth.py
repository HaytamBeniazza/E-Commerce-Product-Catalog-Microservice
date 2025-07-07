"""Authentication API endpoints.

This module provides endpoints for user authentication, registration,
token management, and password operations.
"""

from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import (
    get_db_session,
    get_cache_service,
    get_current_user,
    get_current_active_user
)
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    UserPasswordChange,
    UserPasswordReset,
    UserPasswordResetConfirm,
    TokenResponse,
    TokenRefresh
)
from app.services.auth_service import AuthService
from app.services.cache_service import CacheService

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()
settings = get_settings()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user account with email verification"
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> UserResponse:
    """Register a new user.
    
    Args:
        user_data: User registration data
        db: Database session
        cache: Cache service
        
    Returns:
        User response with tokens
        
    Raises:
        HTTPException: If registration fails
    """
    auth_service = AuthService(db, cache)
    
    try:
        user, tokens = await auth_service.register_user(user_data)
        return UserResponse(
            user=user,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate user and return access tokens"
)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> TokenResponse:
    """Authenticate user and return tokens.
    
    Args:
        credentials: User login credentials
        db: Database session
        cache: Cache service
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    auth_service = AuthService(db, cache)
    
    try:
        user, tokens = await auth_service.authenticate_user(
            credentials.email_or_username,
            credentials.password
        )
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
            expires_in=int(timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES).total_seconds())
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get new access token using refresh token"
)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> TokenResponse:
    """Refresh access token.
    
    Args:
        token_data: Refresh token data
        db: Database session
        cache: Cache service
        
    Returns:
        New access and refresh tokens
        
    Raises:
        HTTPException: If token refresh fails
    """
    auth_service = AuthService(db, cache)
    
    try:
        tokens = await auth_service.refresh_token(token_data.refresh_token)
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
            expires_in=int(timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES).total_seconds())
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post(
    "/logout",
    response_model=SuccessResponse,
    summary="User logout",
    description="Logout user and invalidate tokens"
)
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> SuccessResponse:
    """Logout user and invalidate tokens.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        cache: Cache service
        
    Returns:
        Success response
    """
    auth_service = AuthService(db, cache)
    await auth_service.logout_user(str(current_user.id))
    
    return SuccessResponse(
        message="Successfully logged out",
        data={"user_id": str(current_user.id)}
    )


@router.get(
    "/me",
    response_model=User,
    summary="Get current user",
    description="Get current authenticated user information"
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user data
    """
    return current_user


@router.put(
    "/me",
    response_model=User,
    summary="Update current user",
    description="Update current authenticated user information"
)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> User:
    """Update current user information.
    
    Args:
        user_data: User update data
        current_user: Current authenticated user
        db: Database session
        cache: Cache service
        
    Returns:
        Updated user data
        
    Raises:
        HTTPException: If update fails
    """
    auth_service = AuthService(db, cache)
    
    try:
        updated_user = await auth_service.update_user(
            str(current_user.id),
            user_data
        )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/change-password",
    response_model=SuccessResponse,
    summary="Change password",
    description="Change current user password"
)
async def change_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> SuccessResponse:
    """Change user password.
    
    Args:
        password_data: Password change data
        current_user: Current authenticated user
        db: Database session
        cache: Cache service
        
    Returns:
        Success response
        
    Raises:
        HTTPException: If password change fails
    """
    auth_service = AuthService(db, cache)
    
    try:
        await auth_service.change_password(
            str(current_user.id),
            password_data.current_password,
            password_data.new_password
        )
        
        return SuccessResponse(
            message="Password changed successfully",
            data={"user_id": str(current_user.id)}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/forgot-password",
    response_model=SuccessResponse,
    summary="Request password reset",
    description="Request password reset email"
)
async def forgot_password(
    reset_data: UserPasswordReset,
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> SuccessResponse:
    """Request password reset.
    
    Args:
        reset_data: Password reset request data
        db: Database session
        cache: Cache service
        
    Returns:
        Success response
    """
    auth_service = AuthService(db, cache)
    
    try:
        await auth_service.request_password_reset(reset_data.email)
        
        return SuccessResponse(
            message="Password reset email sent if account exists",
            data={"email": reset_data.email}
        )
    except Exception:
        # Always return success for security reasons
        return SuccessResponse(
            message="Password reset email sent if account exists",
            data={"email": reset_data.email}
        )


@router.post(
    "/reset-password",
    response_model=SuccessResponse,
    summary="Reset password",
    description="Reset password using reset token"
)
async def reset_password(
    reset_data: UserPasswordResetConfirm,
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> SuccessResponse:
    """Reset password using token.
    
    Args:
        reset_data: Password reset confirmation data
        db: Database session
        cache: Cache service
        
    Returns:
        Success response
        
    Raises:
        HTTPException: If password reset fails
    """
    auth_service = AuthService(db, cache)
    
    try:
        await auth_service.reset_password(
            reset_data.token,
            reset_data.new_password
        )
        
        return SuccessResponse(
            message="Password reset successfully",
            data={"token": reset_data.token[:8] + "..."}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/verify-email/{token}",
    response_model=SuccessResponse,
    summary="Verify email",
    description="Verify user email using verification token"
)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> SuccessResponse:
    """Verify user email.
    
    Args:
        token: Email verification token
        db: Database session
        cache: Cache service
        
    Returns:
        Success response
        
    Raises:
        HTTPException: If email verification fails
    """
    auth_service = AuthService(db, cache)
    
    try:
        user = await auth_service.verify_email(token)
        
        return SuccessResponse(
            message="Email verified successfully",
            data={
                "user_id": str(user.id),
                "email": user.email
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/resend-verification",
    response_model=SuccessResponse,
    summary="Resend verification email",
    description="Resend email verification link"
)
async def resend_verification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service)
) -> SuccessResponse:
    """Resend email verification.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        cache: Cache service
        
    Returns:
        Success response
        
    Raises:
        HTTPException: If user already verified
    """
    if current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    auth_service = AuthService(db, cache)
    
    try:
        await auth_service.send_verification_email(current_user.email)
        
        return SuccessResponse(
            message="Verification email sent",
            data={"email": current_user.email}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )