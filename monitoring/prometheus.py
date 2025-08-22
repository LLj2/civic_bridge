"""
Prometheus Metrics for Civic Bridge
Provides application metrics for monitoring and alerting
"""

import time
import logging
from functools import wraps
from typing import Dict, Any
from datetime import datetime

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from flask import request, Response, current_app

logger = logging.getLogger(__name__)

# Application info
app_info = Info('civic_bridge_app_info', 'Application information')
app_info.info({
    'version': '2.0.0',
    'name': 'civic-bridge'
})

# Request metrics
request_count = Counter(
    'civic_bridge_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

request_duration = Histogram(
    'civic_bridge_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Database metrics
db_query_count = Counter(
    'civic_bridge_db_queries_total',
    'Total number of database queries',
    ['query_type', 'table']
)

db_query_duration = Histogram(
    'civic_bridge_db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type', 'table']
)

db_connection_pool = Gauge(
    'civic_bridge_db_connection_pool',
    'Database connection pool status',
    ['status']
)

# Cache metrics
cache_operations = Counter(
    'civic_bridge_cache_operations_total',
    'Total cache operations',
    ['operation', 'result']
)

cache_hit_ratio = Gauge(
    'civic_bridge_cache_hit_ratio',
    'Cache hit ratio percentage'
)

# Application-specific metrics
autocomplete_requests = Counter(
    'civic_bridge_autocomplete_requests_total',
    'Total autocomplete requests',
    ['query_length']
)

lookup_requests = Counter(
    'civic_bridge_lookup_requests_total',
    'Total lookup requests',
    ['has_results']
)

representative_queries = Counter(
    'civic_bridge_representative_queries_total',
    'Total representative queries',
    ['institution']
)

# System metrics
active_users = Gauge(
    'civic_bridge_active_users',
    'Number of active users'
)

data_freshness = Gauge(
    'civic_bridge_data_freshness_hours',
    'Hours since last data update',
    ['data_type']
)

# Error metrics
error_count = Counter(
    'civic_bridge_errors_total',
    'Total number of errors',
    ['error_type', 'endpoint']
)

class MetricsCollector:
    """Collect and manage application metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_update = datetime.utcnow()
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        request_count.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_db_query(self, query_type: str, table: str, duration: float):
        """Record database query metrics"""
        db_query_count.labels(
            query_type=query_type,
            table=table
        ).inc()
        
        db_query_duration.labels(
            query_type=query_type,
            table=table
        ).observe(duration)
    
    def record_cache_operation(self, operation: str, result: str):
        """Record cache operation metrics"""
        cache_operations.labels(
            operation=operation,
            result=result
        ).inc()
    
    def update_cache_hit_ratio(self, ratio: float):
        """Update cache hit ratio gauge"""
        cache_hit_ratio.set(ratio)
    
    def record_autocomplete_request(self, query_length: int):
        """Record autocomplete request metrics"""
        length_bucket = self._get_query_length_bucket(query_length)
        autocomplete_requests.labels(query_length=length_bucket).inc()
    
    def record_lookup_request(self, has_results: bool):
        """Record lookup request metrics"""
        lookup_requests.labels(has_results=str(has_results)).inc()
    
    def record_representative_query(self, institution: str):
        """Record representative query metrics"""
        representative_queries.labels(institution=institution).inc()
    
    def record_error(self, error_type: str, endpoint: str):
        """Record error metrics"""
        error_count.labels(
            error_type=error_type,
            endpoint=endpoint
        ).inc()
    
    def update_db_connection_pool(self, active: int, idle: int, total: int):
        """Update database connection pool metrics"""
        db_connection_pool.labels(status='active').set(active)
        db_connection_pool.labels(status='idle').set(idle)
        db_connection_pool.labels(status='total').set(total)
    
    def update_data_freshness(self, data_type: str, hours_old: float):
        """Update data freshness metrics"""
        data_freshness.labels(data_type=data_type).set(hours_old)
    
    def _get_query_length_bucket(self, length: int) -> str:
        """Get query length bucket for metrics"""
        if length <= 2:
            return '1-2'
        elif length <= 5:
            return '3-5'
        elif length <= 10:
            return '6-10'
        else:
            return '10+'

# Global metrics collector
metrics = MetricsCollector()

def track_requests():
    """Decorator to track HTTP request metrics"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            try:
                response = f(*args, **kwargs)
                status_code = getattr(response, 'status_code', 200)
                
                # Record metrics
                duration = time.time() - start_time
                metrics.record_request(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown',
                    status_code=status_code,
                    duration=duration
                )
                
                return response
                
            except Exception as e:
                # Record error
                duration = time.time() - start_time
                metrics.record_error(
                    error_type=type(e).__name__,
                    endpoint=request.endpoint or 'unknown'
                )
                
                metrics.record_request(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown',
                    status_code=500,
                    duration=duration
                )
                
                raise
        
        return decorated_function
    return decorator

def track_db_query(query_type: str, table: str):
    """Decorator to track database query metrics"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time
                metrics.record_db_query(query_type, table, duration)
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_db_query(f"{query_type}_error", table, duration)
                raise
        
        return decorated_function
    return decorator

def track_cache_operation(operation: str):
    """Decorator to track cache operation metrics"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                
                # Determine if operation was successful
                if operation in ['get']:
                    result_type = 'hit' if result is not None else 'miss'
                elif operation in ['set', 'delete']:
                    result_type = 'success' if result else 'failure'
                else:
                    result_type = 'success'
                
                metrics.record_cache_operation(operation, result_type)
                return result
                
            except Exception as e:
                metrics.record_cache_operation(operation, 'error')
                raise
        
        return decorated_function
    return decorator

def init_metrics(app):
    """Initialize metrics collection with Flask app"""
    
    @app.before_request
    def before_request():
        """Set request start time"""
        request.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """Record request metrics"""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            metrics.record_request(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status_code=response.status_code,
                duration=duration
            )
        
        return response
    
    @app.route('/metrics')
    def metrics_endpoint():
        """Prometheus metrics endpoint"""
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
    
    logger.info("Metrics collection initialized")

def collect_system_metrics():
    """Collect system-level metrics"""
    try:
        # Update cache hit ratio
        from cache import get_cache_stats
        cache_stats = get_cache_stats()
        if 'cache_hit_ratio' in cache_stats:
            metrics.update_cache_hit_ratio(cache_stats['cache_hit_ratio'])
        
        # Update database connection pool info
        from database.models import db
        engine = db.engine
        pool = engine.pool
        
        if hasattr(pool, 'checkedout'):
            active = pool.checkedout()
            idle = pool.size() - active
            total = pool.size()
            metrics.update_db_connection_pool(active, idle, total)
        
        # Update data freshness
        from database.repository import CivicBridgeRepository
        repo = CivicBridgeRepository()
        health_stats = repo.get_health_stats()
        
        if 'last_updated' in health_stats and health_stats['last_updated']:
            last_update = health_stats['last_updated']
            hours_old = (datetime.utcnow() - last_update).total_seconds() / 3600
            metrics.update_data_freshness('comuni', hours_old)
        
    except Exception as e:
        logger.warning(f"Error collecting system metrics: {e}")

class HealthChecker:
    """Health check endpoint with metrics"""
    
    @staticmethod
    def get_health_status() -> Dict[str, Any]:
        """Get comprehensive health status"""
        try:
            from database.repository import CivicBridgeRepository
            from cache import get_cache_stats
            
            repo = CivicBridgeRepository()
            
            # Database health
            db_stats = repo.get_health_stats()
            db_healthy = db_stats.get('database_status') == 'healthy'
            
            # Cache health
            cache_stats = get_cache_stats()
            cache_healthy = 'error' not in cache_stats
            
            # Overall health
            overall_healthy = db_healthy and cache_healthy
            
            return {
                'status': 'healthy' if overall_healthy else 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'service': 'civic-bridge-api',
                'version': '2.0.0',
                'components': {
                    'database': {
                        'status': 'healthy' if db_healthy else 'unhealthy',
                        'details': db_stats
                    },
                    'cache': {
                        'status': 'healthy' if cache_healthy else 'unhealthy',
                        'details': cache_stats
                    }
                },
                'metrics': {
                    'uptime_seconds': time.time() - metrics.start_time,
                    'requests_total': request_count._value._value,
                    'errors_total': error_count._value._value
                }
            }
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }