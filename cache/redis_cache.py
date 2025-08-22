"""
Redis Caching Layer for Civic Bridge
Provides caching functionality for improved performance
"""

import json
import pickle
import hashlib
import logging
from functools import wraps
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta

import redis
from flask import current_app, request
from flask_caching import Cache

logger = logging.getLogger(__name__)

class CivicBridgeCache:
    """Enhanced caching system for Civic Bridge"""
    
    def __init__(self, app=None):
        self.redis_client = None
        self.flask_cache = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize caching with Flask app"""
        try:
            # Initialize Redis client
            redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            self.redis_client.ping()
            
            # Initialize Flask-Caching
            app.config.setdefault('CACHE_TYPE', 'redis')
            app.config.setdefault('CACHE_REDIS_URL', redis_url)
            app.config.setdefault('CACHE_DEFAULT_TIMEOUT', 300)
            
            self.flask_cache = Cache(app)
            
            logger.info(f"Cache initialized with Redis at {redis_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache: {e}")
            # Fallback to simple cache for development
            app.config['CACHE_TYPE'] = 'simple'
            self.flask_cache = Cache(app)
            logger.warning("Using simple cache as fallback")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, timeout: int = 300) -> bool:
        """Set value in cache with timeout"""
        try:
            if self.redis_client:
                serialized_value = json.dumps(value, default=str)
                return self.redis_client.setex(key, timeout, serialized_value)
            return False
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            if self.redis_client:
                return bool(self.redis_client.delete(key))
            return False
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete pattern error for pattern {pattern}: {e}")
            return 0
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in cache"""
        try:
            if self.redis_client:
                return self.redis_client.incrby(key, amount)
            return None
        except Exception as e:
            logger.warning(f"Cache increment error for key {key}: {e}")
            return None
    
    def expire(self, key: str, timeout: int) -> bool:
        """Set expiration for existing key"""
        try:
            if self.redis_client:
                return bool(self.redis_client.expire(key, timeout))
            return False
        except Exception as e:
            logger.warning(f"Cache expire error for key {key}: {e}")
            return False

# Global cache instance
cache = CivicBridgeCache()

def make_cache_key(*args, **kwargs):
    """Generate cache key from arguments"""
    # Create a unique key from all arguments
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items()) if kwargs else {},
        'endpoint': request.endpoint if request else 'unknown'
    }
    
    # Create hash of the key data
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"civic_bridge:{key_hash}"

def cached(timeout: int = 300, key_prefix: str = None):
    """Decorator for caching function results"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            if key_prefix:
                cache_key = f"{key_prefix}:{make_cache_key(*args, **kwargs)}"
            else:
                cache_key = f"{f.__name__}:{make_cache_key(*args, **kwargs)}"
            
            # Try to get from cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            try:
                result = f(*args, **kwargs)
                cache.set(cache_key, result, timeout)
                logger.debug(f"Cache set for key: {cache_key}")
                return result
            except Exception as e:
                logger.error(f"Error in cached function {f.__name__}: {e}")
                raise
        
        return decorated_function
    return decorator

def cache_autocomplete_results(timeout: int = 600):
    """Specialized caching for autocomplete results"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract query parameter for cache key
            query = kwargs.get('query') or (args[0] if args else '')
            limit = kwargs.get('limit', 50)
            
            cache_key = f"autocomplete:{query.lower()}:{limit}"
            
            # Check cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute and cache
            result = f(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        
        return decorated_function
    return decorator

def cache_lookup_results(timeout: int = 1800):
    """Specialized caching for lookup results"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract comune parameter for cache key
            comune_name = kwargs.get('comune_name') or (args[0] if args else '')
            provincia = kwargs.get('provincia', '')
            
            cache_key = f"lookup:{comune_name.lower()}:{provincia.lower()}"
            
            # Check cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute and cache
            result = f(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        
        return decorated_function
    return decorator

def cache_representatives_list(timeout: int = 3600):
    """Specialized caching for representatives lists"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create cache key from function name and parameters
            rep_type = f.__name__.replace('get_', '').replace('_representatives', '')
            page = kwargs.get('page', 1)
            per_page = kwargs.get('per_page', 20)
            search = kwargs.get('search', '')
            
            cache_key = f"representatives:{rep_type}:{page}:{per_page}:{search.lower()}"
            
            # Check cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute and cache
            result = f(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        
        return decorated_function
    return decorator

def invalidate_cache_pattern(pattern: str):
    """Invalidate all cache keys matching pattern"""
    return cache.delete_pattern(pattern)

def invalidate_autocomplete_cache():
    """Invalidate all autocomplete cache"""
    return invalidate_cache_pattern("autocomplete:*")

def invalidate_lookup_cache():
    """Invalidate all lookup cache"""
    return invalidate_cache_pattern("lookup:*")

def invalidate_representatives_cache():
    """Invalidate all representatives cache"""
    return invalidate_cache_pattern("representatives:*")

def get_cache_stats() -> Dict:
    """Get cache statistics"""
    try:
        if cache.redis_client:
            info = cache.redis_client.info()
            return {
                'redis_version': info.get('redis_version'),
                'used_memory': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'cache_hit_ratio': calculate_hit_ratio(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }
        else:
            return {'status': 'Cache not available'}
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {'error': str(e)}

def calculate_hit_ratio(hits: int, misses: int) -> float:
    """Calculate cache hit ratio percentage"""
    total = hits + misses
    if total == 0:
        return 0.0
    return round((hits / total) * 100, 2)

def warm_cache_with_common_queries():
    """Pre-populate cache with common queries"""
    common_cities = [
        'Milano', 'Roma', 'Napoli', 'Torino', 'Palermo',
        'Genova', 'Bologna', 'Firenze', 'Bari', 'Catania'
    ]
    
    logger.info("Starting cache warming...")
    
    try:
        # Import here to avoid circular imports
        from database.repository import CivicBridgeRepository
        repo = CivicBridgeRepository()
        
        for city in common_cities:
            try:
                # Warm autocomplete cache
                cache_key = f"autocomplete:{city.lower()}:50"
                results = repo.search_comuni(city, limit=50)
                cache.set(cache_key, results, timeout=3600)
                
                # Warm lookup cache if city exists
                if results:
                    comune = repo.get_comune_by_name(city)
                    if comune:
                        lookup_key = f"lookup:{city.lower()}:"
                        lookup_results = repo.get_representatives_by_comune(comune)
                        cache.set(lookup_key, lookup_results, timeout=3600)
                
                logger.debug(f"Warmed cache for {city}")
                
            except Exception as e:
                logger.warning(f"Failed to warm cache for {city}: {e}")
        
        logger.info("Cache warming completed")
        
    except Exception as e:
        logger.error(f"Cache warming failed: {e}")

class CacheMetrics:
    """Cache metrics collection"""
    
    @staticmethod
    def record_cache_hit(key: str):
        """Record cache hit for monitoring"""
        cache.increment(f"metrics:cache_hits:{datetime.now().strftime('%Y%m%d')}")
        cache.increment(f"metrics:cache_hits_total")
    
    @staticmethod
    def record_cache_miss(key: str):
        """Record cache miss for monitoring"""
        cache.increment(f"metrics:cache_misses:{datetime.now().strftime('%Y%m%d')}")
        cache.increment(f"metrics:cache_misses_total")
    
    @staticmethod
    def get_daily_metrics() -> Dict:
        """Get daily cache metrics"""
        today = datetime.now().strftime('%Y%m%d')
        
        try:
            hits = cache.redis_client.get(f"metrics:cache_hits:{today}") or 0
            misses = cache.redis_client.get(f"metrics:cache_misses:{today}") or 0
            
            return {
                'date': today,
                'hits': int(hits),
                'misses': int(misses),
                'hit_ratio': calculate_hit_ratio(int(hits), int(misses))
            }
        except Exception as e:
            logger.error(f"Error getting daily metrics: {e}")
            return {'error': str(e)}