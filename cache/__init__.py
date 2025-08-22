"""
Caching package for Civic Bridge
"""

from .redis_cache import (
    CivicBridgeCache,
    cache,
    cached,
    cache_autocomplete_results,
    cache_lookup_results,
    cache_representatives_list,
    invalidate_cache_pattern,
    invalidate_autocomplete_cache,
    invalidate_lookup_cache,
    invalidate_representatives_cache,
    get_cache_stats,
    warm_cache_with_common_queries,
    CacheMetrics
)

__all__ = [
    'CivicBridgeCache',
    'cache',
    'cached',
    'cache_autocomplete_results',
    'cache_lookup_results', 
    'cache_representatives_list',
    'invalidate_cache_pattern',
    'invalidate_autocomplete_cache',
    'invalidate_lookup_cache',
    'invalidate_representatives_cache',
    'get_cache_stats',
    'warm_cache_with_common_queries',
    'CacheMetrics'
]