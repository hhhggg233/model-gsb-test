import redis
import json
from flask import current_app

class Cache:
    _instance = None
    _client = None
    _enabled = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def init_app(self, app):
        if app.config.get('USE_REDIS', False):
            try:
                self._client = redis.Redis(
                    host=app.config['REDIS_HOST'],
                    port=app.config['REDIS_PORT'],
                    db=app.config['REDIS_DB'],
                    password=app.config.get('REDIS_PASSWORD'),
                    decode_responses=True
                )
                self._client.ping()
                self._enabled = True
                print("Redis连接成功")
            except Exception as e:
                print(f"Redis连接失败，将使用内存缓存: {e}")
                self._client = None
                self._enabled = False
        else:
            print("Redis未启用，使用内存缓存")
            self._client = None
            self._enabled = False
    
    @property
    def client(self):
        return self._client
    
    def get(self, key):
        try:
            if self._enabled and self._client:
                value = self._client.get(key)
                if value:
                    return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key, value, expire=None):
        try:
            if self._enabled and self._client:
                expire = expire or current_app.config.get('CACHE_EXPIRE', 300)
                self._client.setex(key, expire, json.dumps(value, ensure_ascii=False))
                return True
        except Exception as e:
            print(f"Cache set error: {e}")
        return False
    
    def delete(self, key):
        try:
            if self._enabled and self._client:
                self._client.delete(key)
                return True
        except Exception as e:
            print(f"Cache delete error: {e}")
        return False
    
    def delete_pattern(self, pattern):
        try:
            if self._enabled and self._client:
                keys = self._client.keys(pattern)
                if keys:
                    self._client.delete(*keys)
                return True
        except Exception as e:
            print(f"Cache delete_pattern error: {e}")
        return False
    
    def get_user_cache_key(self, user_id):
        return f"user:{user_id}"
    
    def get_users_list_cache_key(self):
        return "users:list"
    
    def get_messages_cache_key(self, user_id):
        return f"messages:user:{user_id}"

cache = Cache()
