import redis
import json
from config import Config

class RedisClient:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            password=Config.REDIS_PASSWORD,
            decode_responses=True
        )
    
    def set(self, key, value, expire=None):
        """设置缓存，可选过期时间（秒）"""
        if isinstance(value, dict):
            value = json.dumps(value)
        self.redis_client.set(key, value, ex=expire)
    
    def get(self, key):
        """获取缓存"""
        value = self.redis_client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    def delete(self, key):
        """删除缓存"""
        self.redis_client.delete(key)
    
    def exists(self, key):
        """检查key是否存在"""
        return self.redis_client.exists(key)
    
    def set_user_online(self, user_id):
        """设置用户在线状态"""
        self.redis_client.sadd('online_users', user_id)
    
    def set_user_offline(self, user_id):
        """设置用户离线状态"""
        self.redis_client.srem('online_users', user_id)
    
    def get_online_users(self):
        """获取在线用户列表"""
        return list(self.redis_client.smembers('online_users'))
    
    def cache_user(self, user_id, user_data, expire=3600):
        """缓存用户信息"""
        self.set(f'user:{user_id}', user_data, expire)
    
    def get_cached_user(self, user_id):
        """获取缓存的用户信息"""
        return self.get(f'user:{user_id}')
    
    def invalidate_user_cache(self, user_id):
        """使用户缓存失效"""
        self.delete(f'user:{user_id}')

redis_client = RedisClient()
