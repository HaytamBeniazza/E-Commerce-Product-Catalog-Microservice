"""Authentication service for user management and JWT token handling.

This module provides authentication functionality including user registration,
login, password management, and JWT token operations.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import UserCreate, UserLogin, UserPasswordChange, UserPasswordReset
from app.services.cache_service import CacheService


class AuthService:
    """Authentication service for user management."""
    
    def __init__(self, db_session: AsyncSession, cache_service: Optional[CacheService] = None):
        """Initialize authentication service.
        
        Args:
            db_session: Database session
            cache_service: Cache service for storing tokens and user data
        """
        self.db = db_session
        self.cache = cache_service
        self.settings = get_settings()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token.
        
        Args:
            data: Data to encode in token
            expires_delta: Token expiration time
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.settings.SECRET_KEY, algorithm=self.settings.ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token.
        
        Args:
            data: Data to encode in token
            
        Returns:
            JWT refresh token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.settings.SECRET_KEY, algorithm=self.settings.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[dict]:
        """Verify and decode JWT token.
        
        Args:
            token: JWT token string
            token_type: Expected token type (access or refresh)
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.settings.SECRET_KEY, algorithms=[self.settings.ALGORITHM])
            if payload.get("type") != token_type:
                return None
            return payload
        except JWTError:
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address.
        
        Args:
            email: User email address
            
        Returns:
            User object or None if not found
        """
        # Try cache first
        if self.cache:
            cached_user = await self.cache.get_user_by_email(email)
            if cached_user:
                return cached_user
        
        # Query database
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        user = result.scalar_one_or_none()
        
        # Cache user if found
        if user and self.cache:
            await self.cache.set_user(user)
        
        return user
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User object or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.username == username.lower())
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object or None if not found
        """
        # Try cache first
        if self.cache:
            cached_user = await self.cache.get_user(user_id)
            if cached_user:
                return cached_user
        
        # Query database
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        # Cache user if found
        if user and self.cache:
            await self.cache.set_user(user)
        
        return user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password.
        
        Args:
            email: User email address
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            # Increment failed login attempts
            await self._increment_failed_login_attempts(user)
            return None
        
        # Check if user can login
        if not user.can_login:
            return None
        
        # Reset failed login attempts and update last login
        await self._reset_failed_login_attempts(user)
        await self._update_last_login(user)
        
        return user
    
    async def register_user(self, user_data: UserCreate) -> User:
        """Register a new user.
        
        Args:
            user_data: User registration data
            
        Returns:
            Created user object
            
        Raises:
            HTTPException: If email or username already exists
        """
        # Check if email already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists
        existing_username = await self.get_user_by_username(user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user
        hashed_password = self.get_password_hash(user_data.password)
        
        user = User(
            email=user_data.email.lower(),
            username=user_data.username.lower(),
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            bio=user_data.bio,
            timezone=user_data.timezone,
            language=user_data.language,
            role=user_data.role,
            status=UserStatus.ACTIVE,
            is_active=True,
            email_verification_token=secrets.token_urlsafe(32)
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        # Cache user
        if self.cache:
            await self.cache.set_user(user)
        
        return user
    
    async def login_user(self, login_data: UserLogin) -> Tuple[User, str, str]:
        """Login user and generate tokens.
        
        Args:
            login_data: User login data
            
        Returns:
            Tuple of (user, access_token, refresh_token)
            
        Raises:
            HTTPException: If authentication fails
        """
        user = await self.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate tokens
        access_token_expires = timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        if login_data.remember_me:
            access_token_expires = timedelta(days=7)  # Extended expiry for remember me
        
        access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value},
            expires_delta=access_token_expires
        )
        
        refresh_token = self.create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Store refresh token in cache
        if self.cache:
            await self.cache.set_refresh_token(str(user.id), refresh_token)
        
        return user, access_token, refresh_token
    
    async def refresh_access_token(self, refresh_token: str) -> Tuple[str, str]:
        """Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Tuple of (new_access_token, new_refresh_token)
            
        Raises:
            HTTPException: If refresh token is invalid
        """
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Verify refresh token in cache
        if self.cache:
            cached_token = await self.cache.get_refresh_token(user_id)
            if cached_token != refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
        
        # Get user
        user = await self.get_user_by_id(user_id)
        if not user or not user.can_login:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new tokens
        new_access_token = self.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )
        
        new_refresh_token = self.create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Update refresh token in cache
        if self.cache:
            await self.cache.set_refresh_token(str(user.id), new_refresh_token)
        
        return new_access_token, new_refresh_token
    
    async def logout_user(self, user_id: str, refresh_token: Optional[str] = None) -> None:
        """Logout user and invalidate tokens.
        
        Args:
            user_id: User ID
            refresh_token: Refresh token to invalidate
        """
        if self.cache:
            # Remove refresh token from cache
            await self.cache.delete_refresh_token(user_id)
            
            # Remove user from cache
            await self.cache.delete_user(user_id)
    
    async def change_password(self, user_id: str, password_data: UserPasswordChange) -> None:
        """Change user password.
        
        Args:
            user_id: User ID
            password_data: Password change data
            
        Raises:
            HTTPException: If current password is incorrect
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not self.verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        new_hashed_password = self.get_password_hash(password_data.new_password)
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                hashed_password=new_hashed_password,
                password_changed_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        await self.db.commit()
        
        # Clear user cache
        if self.cache:
            await self.cache.delete_user(user_id)
    
    async def request_password_reset(self, email: str) -> str:
        """Request password reset for user.
        
        Args:
            email: User email address
            
        Returns:
            Password reset token
            
        Raises:
            HTTPException: If user not found
        """
        user = await self.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        reset_expires = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        
        # Update user with reset token
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(
                password_reset_token=reset_token,
                password_reset_expires=reset_expires,
                updated_at=datetime.utcnow()
            )
        )
        await self.db.commit()
        
        # Clear user cache
        if self.cache:
            await self.cache.delete_user(str(user.id))
        
        return reset_token
    
    async def reset_password(self, token: str, new_password: str) -> None:
        """Reset user password using reset token.
        
        Args:
            token: Password reset token
            new_password: New password
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        # Find user with reset token
        result = await self.db.execute(
            select(User).where(
                User.password_reset_token == token,
                User.password_reset_expires > datetime.utcnow()
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Update password and clear reset token
        new_hashed_password = self.get_password_hash(new_password)
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(
                hashed_password=new_hashed_password,
                password_reset_token=None,
                password_reset_expires=None,
                password_changed_at=datetime.utcnow(),
                failed_login_attempts=0,
                account_locked_until=None,
                updated_at=datetime.utcnow()
            )
        )
        await self.db.commit()
        
        # Clear user cache
        if self.cache:
            await self.cache.delete_user(str(user.id))
    
    async def verify_email(self, token: str) -> None:
        """Verify user email using verification token.
        
        Args:
            token: Email verification token
            
        Raises:
            HTTPException: If token is invalid
        """
        # Find user with verification token
        result = await self.db.execute(
            select(User).where(User.email_verification_token == token)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        # Update user as verified
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(
                is_verified=True,
                email_verification_token=None,
                email_verified_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        await self.db.commit()
        
        # Clear user cache
        if self.cache:
            await self.cache.delete_user(str(user.id))
    
    async def _increment_failed_login_attempts(self, user: User) -> None:
        """Increment failed login attempts for user.
        
        Args:
            user: User object
        """
        new_attempts = user.failed_login_attempts + 1
        account_locked_until = None
        
        # Lock account if too many failed attempts
        if new_attempts >= self.settings.MAX_LOGIN_ATTEMPTS:
            account_locked_until = datetime.utcnow() + timedelta(
                minutes=self.settings.ACCOUNT_LOCKOUT_DURATION_MINUTES
            )
        
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(
                failed_login_attempts=new_attempts,
                account_locked_until=account_locked_until,
                updated_at=datetime.utcnow()
            )
        )
        await self.db.commit()
        
        # Clear user cache
        if self.cache:
            await self.cache.delete_user(str(user.id))
    
    async def _reset_failed_login_attempts(self, user: User) -> None:
        """Reset failed login attempts for user.
        
        Args:
            user: User object
        """
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(
                failed_login_attempts=0,
                account_locked_until=None,
                updated_at=datetime.utcnow()
            )
        )
        await self.db.commit()
    
    async def _update_last_login(self, user: User) -> None:
        """Update last login time and increment login count.
        
        Args:
            user: User object
        """
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(
                last_login=datetime.utcnow(),
                login_count=user.login_count + 1,
                updated_at=datetime.utcnow()
            )
        )
        await self.db.commit()
        
        # Clear user cache to force refresh
        if self.cache:
            await self.cache.delete_user(str(user.id))