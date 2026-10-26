import os
import re
from dotenv import load_dotenv

load_dotenv()

# Determine database type from DATABASE_URL
_db_uri = os.environ.get('DATABASE_URL') or 'sqlite:///tas_erp.db'
_is_sqlite = _db_uri.startswith('sqlite')

# Engine options based on database type
_ENGINE_OPTIONS_SQLITE = {
    'pool_pre_ping': True,
}

_ENGINE_OPTIONS_OTHER = {
    'pool_pre_ping': True,
    'isolation_level': 'READ COMMITTED',
}

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-please-change'
    # SQLite for easy setup (no MySQL required)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///tas_erp.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = _ENGINE_OPTIONS_SQLITE if _is_sqlite else _ENGINE_OPTIONS_OTHER
    
    # Upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
    
    # CSRF protection
    WTF_CSRF_ENABLED = True
    
    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Security Headers
    SECURITY_HEADERS = {
        'X-Frame-Options': 'DENY',
        'X-Content-Type-Options': 'nosniff',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    # Microsoft Entra ID (Azure AD) SSO Configuration
    AZURE_TENANT_ID = os.environ.get('AZURE_TENANT_ID')
    AZURE_CLIENT_ID = os.environ.get('AZURE_CLIENT_ID')
    AZURE_CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET')
    
    # Dynamic base URL for redirect URI construction
    APP_URL = os.environ.get('APP_URL')
    
    # Derived configuration
    AZURE_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}" if AZURE_TENANT_ID else None
    # Use list format for scopes - MSAL will handle conversion
    AZURE_SCOPE = ["User.Read"]  # Simplified scope - only request what we need
    
    # Rate limiting configuration
    LOGIN_RATE_LIMIT = os.environ.get('LOGIN_RATE_LIMIT', '30 per minute')
    AUTH_INITIATE_RATE_LIMIT = os.environ.get('AUTH_INITIATE_RATE_LIMIT', '20 per minute')
    AUTH_CALLBACK_RATE_LIMIT = os.environ.get('AUTH_CALLBACK_RATE_LIMIT', '30 per minute')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Require HTTPS
    
    # Enhanced database pooling for production
    if _is_sqlite:
        SQLALCHEMY_ENGINE_OPTIONS = {
            **Config.SQLALCHEMY_ENGINE_OPTIONS,
            'pool_size': 5,
            'max_overflow': 10,
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            **Config.SQLALCHEMY_ENGINE_OPTIONS,
            'pool_size': 10,
            'max_overflow': 20,
            'pool_timeout': 30,
            'pool_recycle': 1800,
        }
    
    # Validate SECRET_KEY in production
    @classmethod
    def init_app(cls, app):
        """Initialize production configuration with comprehensive Azure AD validation."""
        Config.init_app(app)
        
        # Existing SECRET_KEY validation
        if not os.environ.get('SECRET_KEY') or cls.SECRET_KEY == 'dev-secret-key-please-change':
            raise ValueError(
                "SECRET_KEY must be set in environment variables for production. "
                "Generate with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        
        # Validate required Azure AD credentials presence
        required_azure_vars = ['AZURE_TENANT_ID', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET', 'APP_URL']
        missing_vars = [var for var in required_azure_vars if not os.environ.get(var)]
        
        if missing_vars:
            raise ValueError(
                f"Missing required Azure AD environment variables: {', '.join(missing_vars)}.\n"
                "Obtain from Azure Portal → App registrations → Your App:\n"
                "  - AZURE_TENANT_ID: Directory (tenant) ID\n"
                "  - AZURE_CLIENT_ID: Application (client) ID\n"
                "  - AZURE_CLIENT_SECRET: Certificates & secrets → New client secret\n"
                "  - APP_URL: Application base URL (e.g., https://yourdomain.com)"
            )
        
        # UUID format validation for tenant and client IDs
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        
        tenant_id = os.environ.get('AZURE_TENANT_ID', '')
        client_id = os.environ.get('AZURE_CLIENT_ID', '')
        
        if tenant_id and not uuid_pattern.match(tenant_id):
            raise ValueError(
                f"AZURE_TENANT_ID is not a valid UUID: {tenant_id}.\n"
                "Check: Azure Portal → App registrations → Overview → Directory (tenant) ID"
            )
        
        if client_id and not uuid_pattern.match(client_id):
            raise ValueError(
                f"AZURE_CLIENT_ID is not a valid UUID: {client_id}.\n"
                "Check: Azure Portal → App registrations → Overview → Application (client) ID"
            )
        
        # Client secret validation (Azure generates 40-44 character secrets)
        client_secret = os.environ.get('AZURE_CLIENT_SECRET', '')
        if client_secret and len(client_secret) < 32:
            raise ValueError(
                f"AZURE_CLIENT_SECRET appears invalid (length: {len(client_secret)} chars, expected 32+).\n"
                "Generate new: Azure Portal → App registrations → Certificates & secrets"
            )
        
        # APP_URL format validation
        app_url = os.environ.get('APP_URL', '')
        if app_url and not (app_url.startswith('http://') or app_url.startswith('https://')):
            raise ValueError(
                f"APP_URL must start with http:// or https://. Got: {app_url}"
            )
        
        # Warn if production uses HTTP (except localhost)
        if app_url and app_url.startswith('http://') and not app_url.startswith('http://localhost'):
            import logging
            logging.warning(
                f"APP_URL uses HTTP in production: {app_url}. "
                "HTTPS is strongly recommended for security."
            )
    
    # Add HSTS header for production
    SECURITY_HEADERS = {
        **Config.SECURITY_HEADERS,
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
