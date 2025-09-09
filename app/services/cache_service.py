"""Redis cache service"""

from typing import Optional, Any
import json
import redis.asyncio as redis
from loguru import logger

from app.config import settings
from app.exceptions import CacheError


class CacheService:
    """Redis cache service for storing invoice processing results"""
    
    def __init__(self):
        self._redis_client: Optional[redis.Redis] = None
    
    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client connection with connection pooling"""
        if self._redis_client is None:
            try:
                self._redis_client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    decode_responses=True,
                    max_connections=10,  # Connection pool for better resource management
                    socket_connect_timeout=5,  # Prevent hanging connections
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                # Test connection
                await self._redis_client.ping()
                logger.info(f"Connected to Redis at {settings.redis_host}:{settings.redis_port}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise CacheError(f"Redis connection failed: {e}")
        return self._redis_client
    
    async def get(self, key: str) -> Optional[dict]:
        """Get value from cache by key"""
        try:
            client = await self._get_client()
            value = await client.get(key)
            if value:
                logger.info(f"Cache hit for key: {key[:8]}...")
                return json.loads(value)
            logger.info(f"Cache miss for key: {key[:8]}...")
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key[:8]}...: {e}")
            return None
    
    async def set(self, key: str, value: dict) -> bool:
        """Set value in cache with 24-hour TTL"""
        try:
            client = await self._get_client()
            json_value = json.dumps(value)
            result = await client.setex(key, 86400, json_value)  # 24 hours = 86400 seconds
            if result:
                logger.info(f"Cache set for key: {key[:8]}...")
                return True
            return False
        except Exception as e:
            logger.error(f"Redis set error for key {key[:8]}...: {e}")
            return False
    
    async def check(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            client = await self._get_client()
            exists = await client.exists(key)
            return bool(exists)
        except Exception as e:
            logger.error(f"Redis check error for key {key[:8]}...: {e}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self._redis_client:
            await self._redis_client.close()
            logger.info("Redis connection closed")


# Global cache service instance
cache_service = CacheService()