from redis import Redis
from typing import Optional, Any
import json
from app.core.config import settings
from loguru import logger

class Cache:
    def __init__(self):
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True
        )
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        try:
            value = self.redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set a value in cache with expiration."""
        try:
            self.redis.setex(
                key,
                expire,
                json.dumps(value)
            )
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache."""
        try:
            self.redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False

# Create a singleton instance
cache = Cache() 