"""Database connection management.

This module handles the database connection setup, session management,
and connection pooling for the PostgreSQL database using SQLAlchemy.
"""

import logging
from typing import AsyncGenerator, Optional

from sqlalchemy import MetaData, event, pool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, QueuePool

from app.config import settings

logger = logging.getLogger(__name__)

# Global variables for database connection
engine = None
SessionLocal = None


class Base(DeclarativeBase):
    """Base class for all database models.
    
    This class provides common functionality and naming conventions
    for all database tables.
    """
    
    # Define naming convention for constraints
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


async def init_db_connection() -> None:
    """Initialize database connection and session factory.
    
    Creates the async engine and session factory for database operations.
    This function should be called during application startup.
    
    Raises:
        Exception: If database connection fails
    """
    global engine, SessionLocal
    
    try:
        # Database URL
        database_url = str(settings.DATABASE_URL)
        
        # Engine configuration
        engine_kwargs = {
            "echo": settings.DEBUG,
            "echo_pool": settings.DEBUG,
            "pool_pre_ping": True,
            "pool_recycle": settings.DB_POOL_RECYCLE,
        }
        
        # Configure connection pool based on environment
        if settings.is_testing:
            # Use NullPool for testing to avoid connection issues
            engine_kwargs["poolclass"] = NullPool
        else:
            # Use QueuePool for production with connection pooling
            engine_kwargs.update({
                "poolclass": QueuePool,
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
                "pool_timeout": settings.DB_POOL_TIMEOUT,
            })
        
        # Create async engine
        engine = create_async_engine(database_url, **engine_kwargs)
        
        # Add connection event listeners
        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set database-specific configurations on connection."""
            if "postgresql" in database_url:
                # PostgreSQL specific settings
                with dbapi_connection.cursor() as cursor:
                    cursor.execute("SET timezone TO 'UTC'")
        
        # Create session factory
        SessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False,
        )
        
        # Test the connection
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        
        logger.info("Database connection initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database connection: {e}")
        raise


async def close_db_connection() -> None:
    """Close database connection.
    
    Properly closes the database engine and cleans up connections.
    This function should be called during application shutdown.
    """
    global engine
    
    if engine:
        try:
            await engine.dispose()
            logger.info("Database connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")
        finally:
            engine = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session.
    
    This function provides a database session for dependency injection
    in FastAPI endpoints. It ensures proper session management with
    automatic cleanup.
    
    Yields:
        AsyncSession: Database session
        
    Raises:
        Exception: If session creation fails
    """
    if not SessionLocal:
        raise RuntimeError("Database not initialized. Call init_db_connection() first.")
    
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def get_db_session_context() -> AsyncSession:
    """Get database session for use in service layer.
    
    This function provides a database session for use outside of
    FastAPI dependency injection (e.g., in service classes).
    
    Returns:
        AsyncSession: Database session
        
    Raises:
        Exception: If session creation fails
    """
    if not SessionLocal:
        raise RuntimeError("Database not initialized. Call init_db_connection() first.")
    
    return SessionLocal()


async def check_db_connection() -> bool:
    """Check if database connection is healthy.
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        if not engine:
            return False
            
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def get_engine():
    """Get the database engine.
    
    Returns:
        AsyncEngine: The database engine instance
        
    Raises:
        RuntimeError: If engine is not initialized
    """
    if not engine:
        raise RuntimeError("Database engine not initialized. Call init_db_connection() first.")
    return engine


def get_session_factory():
    """Get the session factory.
    
    Returns:
        async_sessionmaker: The session factory
        
    Raises:
        RuntimeError: If session factory is not initialized
    """
    if not SessionLocal:
        raise RuntimeError("Session factory not initialized. Call init_db_connection() first.")
    return SessionLocal