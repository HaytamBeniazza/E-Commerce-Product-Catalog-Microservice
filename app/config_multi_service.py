"""Multi-service configuration for microservices architecture.

This configuration demonstrates how to set up the product service
to work in a multi-database microservices environment with
inter-service communication capabilities.
"""

import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, HttpUrl, PostgresDsn, RedisDsn, validator
from pydantic_settings import BaseSettings


class MultiServiceSettings(BaseSettings):
    """Multi-service application settings for microservices architecture."""
    
    # ===========================================
    # SERVICE IDENTITY
    # ===========================================
    
    SERVICE_NAME: str = "product-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_DESCRIPTION: str = "E-Commerce Product Catalog Microservice"
    SERVICE_PORT: int = 8000
    SERVICE_HOST: str = "0.0.0.0"
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "E-Commerce Product Catalog"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "A comprehensive e-commerce product catalog microservice"
    
    # ===========================================
    # DATABASE CONFIGURATION (Service-Specific)
    # ===========================================
    
    # Product Service Database (This service)
    DATABASE_URL: Optional[PostgresDsn] = None
    DATABASE_TEST_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        # Default for product service
        return "postgresql+asyncpg://products_user:products_secure_password@localhost:5432/products_db"
    
    # Database Pool Configuration
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    # ===========================================
    # CACHE CONFIGURATION (Service-Specific)
    # ===========================================
    
    # Redis Configuration (Different DB per service)
    REDIS_URL: Optional[RedisDsn] = None
    REDIS_TEST_URL: Optional[RedisDsn] = None
    
    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        # Product service uses Redis DB 2
        return "redis://localhost:6379/2"
    
    # Cache Configuration
    CACHE_TTL_SECONDS: int = 3600
    CACHE_MAX_CONNECTIONS: int = 10
    
    # ===========================================
    # INTER-SERVICE COMMUNICATION
    # ===========================================
    
    # External Service URLs
    USER_SERVICE_URL: str = "http://localhost:8001"
    ORDER_SERVICE_URL: str = "http://localhost:8002"
    INVENTORY_SERVICE_URL: str = "http://localhost:8003"
    PAYMENT_SERVICE_URL: str = "http://localhost:8004"
    NOTIFICATION_SERVICE_URL: str = "http://localhost:8005"
    
    # Service Discovery
    SERVICE_REGISTRY_URL: Optional[str] = None
    CONSUL_HOST: str = "localhost"
    CONSUL_PORT: int = 8500
    
    # Circuit Breaker Configuration
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 30
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION: str = "httpx.HTTPError"
    
    # Request Timeout Configuration
    HTTP_CLIENT_TIMEOUT: int = 30
    INTER_SERVICE_TIMEOUT: int = 10
    
    # ===========================================
    # MESSAGE QUEUE CONFIGURATION
    # ===========================================
    
    # RabbitMQ Configuration
    RABBITMQ_URL: str = "amqp://ecommerce:rabbitmq_password@localhost:5672/"
    RABBITMQ_EXCHANGE: str = "ecommerce.events"
    RABBITMQ_QUEUE_PREFIX: str = "product-service"
    
    # Event Publishing
    ENABLE_EVENT_PUBLISHING: bool = True
    EVENT_STORE_URL: Optional[str] = None
    
    # ===========================================
    # SECURITY CONFIGURATION
    # ===========================================
    
    # Service-specific security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Inter-service authentication
    SERVICE_TO_SERVICE_SECRET: str = secrets.token_urlsafe(32)
    ENABLE_SERVICE_AUTH: bool = True
    
    # API Keys for external services
    EXTERNAL_API_KEYS: Dict[str, str] = {}
    
    # ===========================================
    # ENVIRONMENT & DEPLOYMENT
    # ===========================================
    
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    TESTING: bool = False
    
    # Kubernetes Configuration
    KUBERNETES_NAMESPACE: str = "ecommerce"
    KUBERNETES_SERVICE_NAME: str = "product-service"
    
    # Health Check Configuration
    HEALTH_CHECK_INTERVAL: int = 30
    HEALTH_CHECK_TIMEOUT: int = 5
    HEALTH_CHECK_RETRIES: int = 3
    
    # ===========================================
    # CORS & NETWORKING
    # ===========================================
    
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # Frontend
        "http://localhost:8080",  # Admin panel
        "http://localhost:4200",  # Angular app
        "http://api-gateway",     # API Gateway
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # ===========================================
    # RATE LIMITING & THROTTLING
    # ===========================================
    
    # Service-specific rate limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 20
    
    # Inter-service rate limiting
    INTER_SERVICE_RATE_LIMIT: int = 1000
    
    # ===========================================
    # MONITORING & OBSERVABILITY
    # ===========================================
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    ENABLE_STRUCTURED_LOGGING: bool = True
    
    # Metrics Configuration
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    PROMETHEUS_ENDPOINT: str = "/metrics"
    
    # Distributed Tracing
    ENABLE_TRACING: bool = True
    JAEGER_AGENT_HOST: str = "localhost"
    JAEGER_AGENT_PORT: int = 6831
    TRACE_SAMPLE_RATE: float = 0.1
    
    # ===========================================
    # BUSINESS LOGIC CONFIGURATION
    # ===========================================
    
    # File Upload Configuration
    UPLOAD_DIR: str = "./uploads/products"
    MAX_FILE_SIZE: int = 5242880  # 5MB
    ALLOWED_IMAGE_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    
    # Search Configuration
    SEARCH_RESULTS_PER_PAGE: int = 20
    MAX_SEARCH_RESULTS: int = 1000
    ENABLE_ELASTICSEARCH: bool = False
    ELASTICSEARCH_URL: Optional[str] = None
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Product-specific settings
    MAX_PRODUCT_IMAGES: int = 10
    MAX_PRODUCT_VARIANTS: int = 50
    ENABLE_PRODUCT_REVIEWS: bool = True
    ENABLE_PRODUCT_RECOMMENDATIONS: bool = True
    
    # ===========================================
    # EXTERNAL INTEGRATIONS
    # ===========================================
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: Optional[str] = None
    S3_ENDPOINT_URL: Optional[str] = None
    
    # CDN Configuration
    CDN_URL: Optional[str] = None
    ENABLE_CDN: bool = False
    
    # Email Configuration (for notifications)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    
    # ===========================================
    # FEATURE FLAGS
    # ===========================================
    
    # Feature toggles
    ENABLE_PRODUCT_ANALYTICS: bool = True
    ENABLE_INVENTORY_SYNC: bool = True
    ENABLE_PRICE_ALERTS: bool = True
    ENABLE_BULK_OPERATIONS: bool = True
    ENABLE_PRODUCT_IMPORT: bool = True
    ENABLE_PRODUCT_EXPORT: bool = True
    
    # Experimental features
    ENABLE_AI_RECOMMENDATIONS: bool = False
    ENABLE_DYNAMIC_PRICING: bool = False
    ENABLE_REAL_TIME_INVENTORY: bool = False
    
    # ===========================================
    # PERFORMANCE TUNING
    # ===========================================
    
    # Application Performance
    WORKER_CONNECTIONS: int = 1000
    KEEPALIVE_TIMEOUT: int = 5
    MAX_CONCURRENT_REQUESTS: int = 100
    
    # Database Performance
    DB_QUERY_TIMEOUT: int = 30
    ENABLE_QUERY_LOGGING: bool = False
    ENABLE_SLOW_QUERY_LOG: bool = True
    SLOW_QUERY_THRESHOLD: float = 1.0
    
    # Cache Performance
    CACHE_COMPRESSION: bool = True
    CACHE_SERIALIZATION: str = "pickle"  # json, pickle, msgpack
    
    # ===========================================
    # UTILITY PROPERTIES
    # ===========================================
    
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
        return "postgresql://products_user:products_secure_password@localhost:5432/products_db"
    
    @property
    def service_urls(self) -> Dict[str, str]:
        """Get all external service URLs."""
        return {
            "user": self.USER_SERVICE_URL,
            "order": self.ORDER_SERVICE_URL,
            "inventory": self.INVENTORY_SERVICE_URL,
            "payment": self.PAYMENT_SERVICE_URL,
            "notification": self.NOTIFICATION_SERVICE_URL,
        }
    
    @property
    def database_config(self) -> Dict[str, Any]:
        """Get database configuration for service."""
        return {
            "url": self.DATABASE_URL,
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_timeout": self.DB_POOL_TIMEOUT,
            "pool_recycle": self.DB_POOL_RECYCLE,
        }
    
    @property
    def redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration for service."""
        return {
            "url": self.REDIS_URL,
            "max_connections": self.CACHE_MAX_CONNECTIONS,
            "ttl": self.CACHE_TTL_SECONDS,
        }
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_prefix = "PRODUCT_SERVICE_"


# Global settings instance
multi_service_settings = MultiServiceSettings()


def get_multi_service_settings() -> MultiServiceSettings:
    """Get multi-service application settings.
    
    This function can be used as a dependency in FastAPI endpoints
    to inject configuration settings for microservices architecture.
    
    Returns:
        MultiServiceSettings: Multi-service configuration settings
    """
    return multi_service_settings


# Environment-specific configurations
class DevelopmentSettings(MultiServiceSettings):
    """Development environment settings."""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    ENABLE_QUERY_LOGGING: bool = True
    TRACE_SAMPLE_RATE: float = 1.0


class ProductionSettings(MultiServiceSettings):
    """Production environment settings."""
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENABLE_QUERY_LOGGING: bool = False
    TRACE_SAMPLE_RATE: float = 0.01
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = True


class TestingSettings(MultiServiceSettings):
    """Testing environment settings."""
    TESTING: bool = True
    DATABASE_URL: str = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_products_db"
    REDIS_URL: str = "redis://localhost:6379/15"
    ENABLE_EVENT_PUBLISHING: bool = False
    ENABLE_METRICS: bool = False
    ENABLE_TRACING: bool = False


def get_settings_by_environment(env: str) -> MultiServiceSettings:
    """Get settings based on environment.
    
    Args:
        env: Environment name (development, production, testing)
        
    Returns:
        MultiServiceSettings: Environment-specific settings
    """
    settings_map = {
        "development": DevelopmentSettings,
        "production": ProductionSettings,
        "testing": TestingSettings,
    }
    
    settings_class = settings_map.get(env.lower(), MultiServiceSettings)
    return settings_class()