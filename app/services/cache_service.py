"""Redis cache service for the e-commerce microservice.

This module provides caching functionality using Redis for improved performance
and reduced database load. It includes methods for caching products, search results,
and other frequently accessed data.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as redis
from redis.asyncio import Redis

from app.config import settings

logger = logging.getLogger(__name__)

# Global Redis connection
redis_client: Optional[Redis] = None


class CacheService:
    """Redis cache service for managing cached data."""
    
    def __init__(self, redis_client: Redis):
        """Initialize cache service with Redis client.
        
        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        self.default_ttl = settings.CACHE_TTL_SECONDS
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            await self.redis.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., 'products:*')
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for pattern {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment numeric value in cache.
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            New value after increment or None if error
        """
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return bool(await self.redis.expire(key, ttl))
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining time to live for key.
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds or None if key doesn't exist
        """
        try:
            ttl = await self.redis.ttl(key)
            return ttl if ttl > 0 else None
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return None
    
    # Product-specific cache methods
    async def cache_product(self, product_id: str, product_data: Dict[str, Any]) -> bool:
        """Cache product data.
        
        Args:
            product_id: Product ID
            product_data: Product data to cache
            
        Returns:
            True if successful, False otherwise
        """
        key = f"product:{product_id}"
        return await self.set(key, product_data)
    
    async def get_cached_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get cached product data.
        
        Args:
            product_id: Product ID
            
        Returns:
            Product data or None if not cached
        """
        key = f"product:{product_id}"
        return await self.get(key)
    
    async def invalidate_product_cache(self, product_id: str) -> bool:
        """Invalidate product cache.
        
        Args:
            product_id: Product ID
            
        Returns:
            True if successful, False otherwise
        """
        key = f"product:{product_id}"
        return await self.delete(key)
    
    async def cache_product_list(
        self,
        cache_key: str,
        products: List[Dict[str, Any]],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache product list (e.g., search results, category products).
        
        Args:
            cache_key: Cache key for the product list
            products: List of products to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        return await self.set(cache_key, products, ttl)
    
    async def get_cached_product_list(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached product list.
        
        Args:
            cache_key: Cache key for the product list
            
        Returns:
            List of products or None if not cached
        """
        return await self.get(cache_key)
    
    # Search cache methods
    async def cache_search_results(
        self,
        search_query: str,
        filters: Dict[str, Any],
        results: List[Dict[str, Any]],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache search results.
        
        Args:
            search_query: Search query string
            filters: Applied filters
            results: Search results to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        # Create cache key from query and filters
        cache_key = self._generate_search_cache_key(search_query, filters)
        return await self.set(cache_key, results, ttl or 1800)  # 30 minutes default
    
    async def get_cached_search_results(
        self,
        search_query: str,
        filters: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results.
        
        Args:
            search_query: Search query string
            filters: Applied filters
            
        Returns:
            Search results or None if not cached
        """
        cache_key = self._generate_search_cache_key(search_query, filters)
        return await self.get(cache_key)
    
    def _generate_search_cache_key(self, query: str, filters: Dict[str, Any]) -> str:
        """Generate cache key for search results.
        
        Args:
            query: Search query
            filters: Search filters
            
        Returns:
            Cache key string
        """
        # Sort filters for consistent key generation
        sorted_filters = json.dumps(filters, sort_keys=True)
        return f"search:{hash(query + sorted_filters)}"
    
    # Analytics cache methods
    async def increment_search_count(self, query: str) -> Optional[int]:
        """Increment search count for analytics.
        
        Args:
            query: Search query
            
        Returns:
            New count or None if error
        """
        key = f"search_count:{hash(query)}"
        return await self.increment(key)
    
    async def increment_product_view_count(self, product_id: str) -> Optional[int]:
        """Increment product view count.
        
        Args:
            product_id: Product ID
            
        Returns:
            New count or None if error
        """
        key = f"product_views:{product_id}"
        return await self.increment(key)
    
    # Session cache methods
    async def cache_user_session(
        self,
        session_id: str,
        user_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache user session data.
        
        Args:
            session_id: Session ID
            user_data: User session data
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        key = f"session:{session_id}"
        session_ttl = ttl or (settings.SESSION_TIMEOUT_MINUTES * 60)
        return await self.set(key, user_data, session_ttl)
    
    async def get_user_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user session data.
        
        Args:
            session_id: Session ID
            
        Returns:
            User session data or None if not found
        """
        key = f"session:{session_id}"
        return await self.get(key)
    
    async def invalidate_user_session(self, session_id: str) -> bool:
        """Invalidate user session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful, False otherwise
        """
        key = f"session:{session_id}"
        return await self.delete(key)


async def init_redis_connection() -> None:
    """Initialize Redis connection.
    
    Creates the Redis client for caching operations.
    This function should be called during application startup.
    
    Raises:
        Exception: If Redis connection fails
    """
    global redis_client
    
    try:
        redis_url = str(settings.REDIS_URL)
        
        # Create Redis client
        redis_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.CACHE_MAX_CONNECTIONS,
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={},
        )
        
        # Test the connection
        await redis_client.ping()
        
        logger.info("Redis connection initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Redis connection: {e}")
        raise


async def close_redis_connection() -> None:
    """Close Redis connection.
    
    Properly closes the Redis client and cleans up connections.
    This function should be called during application shutdown.
    """
    global redis_client
    
    if redis_client:
        try:
            await redis_client.close()
            logger.info("Redis connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
        finally:
            redis_client = None


async def get_cache_service() -> CacheService:
    """Get cache service instance.
    
    This function provides a cache service for dependency injection
    in FastAPI endpoints.
    
    Returns:
        CacheService: Cache service instance
        
    Raises:
        RuntimeError: If Redis is not initialized
    """
    if not redis_client:
        raise RuntimeError("Redis not initialized. Call init_redis_connection() first.")
    
    return CacheService(redis_client)


async def check_redis_connection() -> bool:
    """Check if Redis connection is healthy.
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        if not redis_client:
            return False
            
        await redis_client.ping()
        return True
        
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False