"""
Configuration for Civic Bridge application
"""
import os

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-change-in-production'
    
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
    LOG_LEVEL = 'INFO'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DEVELOPMENT = True
    
    # No-cache headers for development
    SEND_FILE_MAX_AGE_DEFAULT = 0

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

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}