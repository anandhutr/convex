"""
Configuration management for Convex Studio Inventory System
Supports different environments and future upgrade paths.
"""

import os
from pathlib import Path

class Config:
    """Base configuration class"""
    
    # Basic Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database settings
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'inventory.db'
    DATABASE_URL = os.environ.get('DATABASE_URL') or f'sqlite:///{DATABASE_PATH}'
    
    # File upload settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'csv', 'txt'}
    
    # Backup and logging settings
    BACKUP_DIR = os.environ.get('BACKUP_DIR') or 'backups'
    LOGS_DIR = os.environ.get('LOGS_DIR') or 'logs'
    MAX_BACKUP_FILES = int(os.environ.get('MAX_BACKUP_FILES', 30))
    
    # Security settings
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Performance settings
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', 50))
    CACHE_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT', 300))  # 5 minutes
    
    # Feature flags for gradual rollout
    FEATURE_FLAGS = {
        'audit_trail': os.environ.get('ENABLE_AUDIT_TRAIL', 'false').lower() == 'true',
        'user_authentication': os.environ.get('ENABLE_AUTH', 'false').lower() == 'true',
        'api_endpoints': os.environ.get('ENABLE_API', 'false').lower() == 'true',
        'advanced_analytics': os.environ.get('ENABLE_ANALYTICS', 'false').lower() == 'true',
        'barcode_support': os.environ.get('ENABLE_BARCODES', 'false').lower() == 'true',
    }
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create necessary directories
        for directory in [Config.UPLOAD_FOLDER, Config.BACKUP_DIR, Config.LOGS_DIR]:
            Path(directory).mkdir(exist_ok=True)
        
        # Set up logging
        if not app.debug:
            import logging
            from logging.handlers import RotatingFileHandler
            
            log_file = Path(Config.LOGS_DIR) / 'inventory.log'
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=10240, 
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Inventory startup')

class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    
    # Development-specific settings
    DATABASE_PATH = 'inventory_dev.db'
    LOG_LEVEL = 'DEBUG'
    
    # Enable all features in development
    FEATURE_FLAGS = {
        'audit_trail': True,
        'user_authentication': True,
        'api_endpoints': True,
        'advanced_analytics': True,
        'barcode_support': True,
    }

class TestingConfig(Config):
    """Testing environment configuration"""
    DEBUG = True
    TESTING = True
    
    # Use in-memory database for testing
    DATABASE_PATH = ':memory:'
    
    # Disable features that might interfere with testing
    FEATURE_FLAGS = {
        'audit_trail': False,
        'user_authentication': False,
        'api_endpoints': False,
        'advanced_analytics': False,
        'barcode_support': False,
    }

class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Production performance settings
    ITEMS_PER_PAGE = 100
    CACHE_TIMEOUT = 600  # 10 minutes
    
    # Production feature flags (enable gradually)
    FEATURE_FLAGS = {
        'audit_trail': os.environ.get('ENABLE_AUDIT_TRAIL', 'true').lower() == 'true',
        'user_authentication': os.environ.get('ENABLE_AUTH', 'true').lower() == 'true',
        'api_endpoints': os.environ.get('ENABLE_API', 'false').lower() == 'true',
        'advanced_analytics': os.environ.get('ENABLE_ANALYTICS', 'false').lower() == 'true',
        'barcode_support': os.environ.get('ENABLE_BARCODES', 'false').lower() == 'true',
    }
    
    @classmethod
    def init_app(cls, app):
        """Initialize production application"""
        Config.init_app(app)
        
        # Production-specific logging
        import logging
        from logging.handlers import SMTPHandler
        
        # Email error reports in production
        if os.environ.get('MAIL_SERVER'):
            auth = None
            if os.environ.get('MAIL_USERNAME') or os.environ.get('MAIL_PASSWORD'):
                auth = (os.environ.get('MAIL_USERNAME'), os.environ.get('MAIL_PASSWORD'))
            secure = None
            if os.environ.get('MAIL_USE_TLS'):
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(os.environ.get('MAIL_SERVER'), os.environ.get('MAIL_PORT')),
                fromaddr=os.environ.get('MAIL_SENDER'),
                toaddrs=[os.environ.get('ADMIN_EMAIL')],
                subject='Inventory System Error',
                credentials=auth,
                secure=secure
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

class StagingConfig(Config):
    """Staging environment configuration"""
    DEBUG = False
    TESTING = False
    
    # Staging settings (similar to production but with debugging)
    DATABASE_PATH = 'inventory_staging.db'
    LOG_LEVEL = 'INFO'
    
    # Enable most features in staging for testing
    FEATURE_FLAGS = {
        'audit_trail': True,
        'user_authentication': True,
        'api_endpoints': True,
        'advanced_analytics': True,
        'barcode_support': True,
    }

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'staging': StagingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])

def is_feature_enabled(feature_name):
    """Check if a feature is enabled in current configuration"""
    config_class = get_config()
    return config_class.FEATURE_FLAGS.get(feature_name, False)

def get_database_path():
    """Get database path from configuration"""
    config_class = get_config()
    return config_class.DATABASE_PATH

def get_upload_folder():
    """Get upload folder path from configuration"""
    config_class = get_config()
    return config_class.UPLOAD_FOLDER 