NEW_FILE_CODE
import redis
import json
import os
from typing import Optional, Any

class RedisClient:
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.client = redis.Redis.from_url(redis_url, decode_responses=True)
            self.client.ping()
            print("✅ Redis connected successfully.")
        except Exception as e:
            print(f"⚠️ Warning: Could not connect to Redis: {e}")
            self.client = None

    def get_cache(self, key: str) -> Optional[Any]:
        if not self.client: return None
        try:
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            return None

    def set_cache(self, key: str, value: dict, expire: int = 1800) -> bool:
        if not self.client: return False
        try:
            self.client.setex(key, expire, json.dumps(value))
            return True
        except Exception as e:
            return False

redis_client = RedisClient()
