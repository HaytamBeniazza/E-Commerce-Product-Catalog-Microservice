"""Application configuration management.

This module handles all configuration settings for the e-commerce microservice,
including database connections, Redis settings, authentication, and various
application parameters.
"""

import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, HttpUrl, PostgresDsn, RedisDsn, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "E-Commerce Product Catalog"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "A comprehensive e-commerce product catalog microservice"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    TESTING: bool = False
    
    # Database Configuration
    DATABASE_URL: Optional[PostgresDsn] = None
    DATABASE_TEST_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return "postgresql+asyncpg://ecommerce_user:ecommerce_password@localhost:5432/ecommerce_db"
    
    # Redis Configuration
    REDIS_URL: Optional[RedisDsn] = None
    REDIS_TEST_URL: Optional[RedisDsn] = None
    
    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return "redis://localhost:6379/0"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:4200",
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    
    # File Upload Configuration
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 5242880  # 5MB in bytes
    ALLOWED_IMAGE_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    
    # AWS S3 Configuration (Optional)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: Optional[str] = None
    S3_ENDPOINT_URL: Optional[str] = None
    
    # Email Configuration (Optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Monitoring and Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # Cache Configuration
    CACHE_TTL_SECONDS: int = 3600
    CACHE_MAX_CONNECTIONS: int = 10
    
    # Search Configuration
    SEARCH_RESULTS_PER_PAGE: int = 20
    MAX_SEARCH_RESULTS: int = 1000
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Security
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Session Configuration
    SESSION_TIMEOUT_MINUTES: int = 60
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    
    # Database Pool Configuration
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    # Application Performance
    WORKER_CONNECTIONS: int = 1000
    KEEPALIVE_TIMEOUT: int = 5
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.TESTING or self.ENVIRONMENT.lower() == "testing"
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic."""
        if self.DATABASE_URL:
            return str(self.DATABASE_URL).replace("+asyncpg", "")
        return "postgresql://ecommerce_user:ecommerce_password@localhost:5432/ecommerce_db"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings.
    
    This function can be used as a dependency in FastAPI endpoints
    to inject configuration settings.
    
    Returns:
        Settings: Application configuration settings
    """
    return settings