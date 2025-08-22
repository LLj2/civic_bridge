"""
Configuration for Civic Bridge application
"""
import os
from urllib.parse import quote_plus

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-change-in-production'
    
    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        # Fallback to individual components
        DB_USER = os.environ.get('DB_USER', 'civic_bridge_user')
        DB_PASSWORD = os.environ.get('DB_PASSWORD', 'civic_bridge_dev_password')
        DB_HOST = os.environ.get('DB_HOST', 'localhost')
        DB_PORT = os.environ.get('DB_PORT', '5432')
        DB_NAME = os.environ.get('DB_NAME', 'civic_bridge')
        DATABASE_URL = f'postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # Redis configuration
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Cache configuration
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/1')
    
    # CORS settings
    CORS_ORIGINS = [
        'http://localhost:5000',
        'http://127.0.0.1:5000'
    ]
    
    # Security settings
    CSP_POLICY = {
        'default-src': "'self'",
        'img-src': "'self' data:",
        'style-src': "'self'",
        'script-src': "'self'"
    }
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', '/app/logs/civic_bridge.log')
    
    # OAuth settings
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    OAUTH_REDIRECT_URI = os.environ.get('OAUTH_REDIRECT_URI', 'http://localhost:5000/auth/google/callback')
    
    # Monitoring
    PROMETHEUS_METRICS = os.environ.get('PROMETHEUS_METRICS', 'false').lower() == 'true'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DEVELOPMENT = True
    
    # No-cache headers for development
    SEND_FILE_MAX_AGE_DEFAULT = 0
    
    # Use SQLite for development if no DATABASE_URL set
    if not os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = 'sqlite:///civic_bridge_dev.db'
        SQLALCHEMY_ENGINE_OPTIONS = {}
    
    # Development cache settings
    CACHE_DEFAULT_TIMEOUT = 60  # 1 minute for faster development

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    DEVELOPMENT = False
    
    # Production security
    CSP_POLICY = {
        **Config.CSP_POLICY,
        'upgrade-insecure-requests': True
    }
    
    # Cache settings
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year
    CACHE_DEFAULT_TIMEOUT = 900  # 15 minutes
    
    # Production database connection pool
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 1800,
        'pool_pre_ping': True,
        'max_overflow': 40,
        'pool_timeout': 30
    }

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Use in-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}
    
    # Disable caching for tests
    CACHE_TYPE = 'null'
    
    # No rate limiting in tests
    RATELIMIT_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}