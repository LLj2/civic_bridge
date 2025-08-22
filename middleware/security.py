"""
Security middleware for Civic Bridge
Includes rate limiting, input validation, and security headers
"""

from functools import wraps
from flask import request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import re
import html
import logging

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"]
)

def init_security_middleware(app):
    """Initialize all security middleware"""
    
    # Initialize rate limiter
    limiter.init_app(app)
    
    # Initialize Talisman for security headers
    csp = {
        'default-src': "'self'",
        'script-src': "'self'",
        'style-src': "'self' 'unsafe-inline'",  # Allow inline styles for now
        'img-src': "'self' data:",
        'font-src': "'self'",
        'connect-src': "'self'",
        'frame-ancestors': "'none'",
        'form-action': "'self'"
    }
    
    Talisman(
        app,
        force_https=False,  # Set to True in production with proper SSL
        strict_transport_security=True,
        content_security_policy=csp,
        x_content_type_options=True,
        x_frame_options='DENY',
        x_xss_protection=True,
        referrer_policy='strict-origin-when-cross-origin'
    )
    
    logger.info("Security middleware initialized")

class InputValidator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_query_string(query: str, max_length: int = 100) -> str:
        """Validate and sanitize search query strings"""
        if not query:
            raise ValueError("Query cannot be empty")
        
        # Remove extra whitespace
        query = query.strip()
        
        if len(query) < 2:
            raise ValueError("Query must be at least 2 characters long")
        
        if len(query) > max_length:
            raise ValueError(f"Query must be no more than {max_length} characters")
        
        # Remove HTML tags and escape special characters
        query = html.escape(query)
        
        # Allow only alphanumeric, spaces, apostrophes, hyphens, and basic punctuation
        if not re.match(r"^[a-zA-ZÀ-ÿ0-9\s'\-\.\,\(\)]+$", query):
            raise ValueError("Query contains invalid characters")
        
        return query
    
    @staticmethod
    def validate_comune_name(comune: str) -> str:
        """Validate Italian comune names"""
        if not comune:
            raise ValueError("Comune name cannot be empty")
        
        comune = comune.strip()
        
        if len(comune) < 2:
            raise ValueError("Comune name must be at least 2 characters long")
        
        if len(comune) > 100:
            raise ValueError("Comune name is too long")
        
        # Italian comune names can have letters, spaces, apostrophes, hyphens
        if not re.match(r"^[a-zA-ZÀ-ÿ\s'\-\.]+$", comune):
            raise ValueError("Invalid characters in comune name")
        
        return html.escape(comune)
    
    @staticmethod
    def validate_provincia_code(provincia: str) -> str:
        """Validate Italian provincia codes (2-3 characters)"""
        if not provincia:
            raise ValueError("Provincia code cannot be empty")
        
        provincia = provincia.strip().upper()
        
        if len(provincia) < 2 or len(provincia) > 3:
            raise ValueError("Provincia code must be 2-3 characters")
        
        if not re.match(r"^[A-Z]+$", provincia):
            raise ValueError("Provincia code must contain only letters")
        
        return provincia
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Basic email validation"""
        if not email:
            raise ValueError("Email cannot be empty")
        
        email = email.strip().lower()
        
        # Basic email regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        if len(email) > 254:  # RFC 5321 limit
            raise ValueError("Email address is too long")
        
        return email
    
    @staticmethod
    def validate_pagination(page: str, per_page: str) -> tuple:
        """Validate pagination parameters"""
        try:
            page = int(page) if page else 1
            per_page = int(per_page) if per_page else 20
        except ValueError:
            raise ValueError("Page and per_page must be integers")
        
        if page < 1:
            raise ValueError("Page must be greater than 0")
        
        if per_page < 1 or per_page > 100:
            raise ValueError("Per page must be between 1 and 100")
        
        return page, per_page

def validate_input(validator_func):
    """Decorator for input validation"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Apply validation based on the validator function
                if validator_func:
                    validated_data = validator_func(request)
                    # Add validated data to kwargs
                    kwargs['validated_data'] = validated_data
                
                return f(*args, **kwargs)
                
            except ValueError as e:
                logger.warning(f"Input validation error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'error_type': 'validation_error'
                }), 400
            except Exception as e:
                logger.error(f"Unexpected validation error: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Invalid request'
                }), 400
        
        return decorated_function
    return decorator

def validate_autocomplete_request(request):
    """Validate autocomplete request parameters"""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', '50')
    
    # Validate query
    validated_query = InputValidator.validate_query_string(query, max_length=100)
    
    # Validate limit
    try:
        validated_limit = int(limit)
        if validated_limit < 1 or validated_limit > 100:
            raise ValueError("Limit must be between 1 and 100")
    except ValueError:
        raise ValueError("Limit must be a valid integer")
    
    return {
        'query': validated_query,
        'limit': validated_limit
    }

def validate_lookup_request(request):
    """Validate lookup request parameters"""
    query = request.args.get('q', '').strip()
    
    validated_query = InputValidator.validate_comune_name(query)
    
    return {
        'query': validated_query
    }

def validate_representatives_request(request):
    """Validate representatives list request"""
    page = request.args.get('page', '1')
    per_page = request.args.get('per_page', '20')
    search = request.args.get('search', '').strip()
    
    validated_page, validated_per_page = InputValidator.validate_pagination(page, per_page)
    
    validated_search = ''
    if search:
        validated_search = InputValidator.validate_query_string(search, max_length=50)
    
    return {
        'page': validated_page,
        'per_page': validated_per_page,
        'search': validated_search
    }

# Rate limiting decorators for different endpoint types
def rate_limit_api():
    """Rate limiting for API endpoints"""
    return limiter.limit("100 per minute")

def rate_limit_autocomplete():
    """Rate limiting for autocomplete endpoints"""
    return limiter.limit("300 per minute")

def rate_limit_search():
    """Rate limiting for search endpoints"""
    return limiter.limit("200 per minute")

def rate_limit_general():
    """General rate limiting for web pages"""
    return limiter.limit("500 per minute")

# Security logging decorator
def log_security_event(event_type: str):
    """Decorator to log security events"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                
                # Log successful requests for monitoring
                if hasattr(result, 'status_code') and result.status_code >= 400:
                    logger.warning(f"Security event {event_type}: {request.remote_addr} - {request.path} - Status: {result.status_code}")
                
                return result
                
            except Exception as e:
                logger.error(f"Security event {event_type}: {request.remote_addr} - {request.path} - Error: {str(e)}")
                raise
        
        return decorated_function
    return decorator