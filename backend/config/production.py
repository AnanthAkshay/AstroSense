"""
Production configuration for AstroSense backend.
Implements connection pooling, logging, and monitoring for production deployment.
"""

import os
import logging
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker


class ProductionConfig:
    """Production configuration with connection pooling and monitoring."""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.pool_size = int(os.getenv('DATABASE_POOL_SIZE', '20'))
        self.max_overflow = int(os.getenv('DATABASE_MAX_OVERFLOW', '30'))
        self.pool_timeout = int(os.getenv('DATABASE_POOL_TIMEOUT', '30'))
        self.pool_recycle = int(os.getenv('DATABASE_POOL_RECYCLE', '3600'))
        self.echo = os.getenv('DATABASE_ECHO', 'false').lower() == 'true'
        
        # CORS configuration
        self.cors_origins = os.getenv('CORS_ORIGINS', '').split(',')
        self.cors_allow_credentials = os.getenv('CORS_ALLOW_CREDENTIALS', 'true').lower() == 'true'
        self.cors_allow_methods = os.getenv('CORS_ALLOW_METHODS', 'GET,POST,PUT,DELETE,OPTIONS').split(',')
        self.cors_allow_headers = os.getenv('CORS_ALLOW_HEADERS', '*').split(',')
        
        # API configuration
        self.api_workers = int(os.getenv('API_WORKERS', '4'))
        self.max_concurrent_requests = int(os.getenv('MAX_CONCURRENT_REQUESTS', '100'))
        self.request_timeout = int(os.getenv('REQUEST_TIMEOUT', '30'))
        
        # Logging configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_format = os.getenv('LOG_FORMAT', 'json')
        self.log_file = os.getenv('LOG_FILE', '/app/logs/astrosense.log')
        
        # Monitoring
        self.enable_metrics = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
        self.metrics_port = int(os.getenv('METRICS_PORT', '9090'))
        
        # Initialize database engine with connection pooling
        self._engine = None
        self._session_factory = None
        
    def get_database_engine(self):
        """Get database engine with connection pooling configured."""
        if self._engine is None:
            self._engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_recycle=self.pool_recycle,
                echo=self.echo,
                # Connection pool settings for production
                pool_pre_ping=True,  # Verify connections before use
                pool_reset_on_return='commit',  # Reset connections on return
            )
        return self._engine
    
    def get_session_factory(self):
        """Get SQLAlchemy session factory."""
        if self._session_factory is None:
            engine = self.get_database_engine()
            self._session_factory = sessionmaker(
                bind=engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
        return self._session_factory
    
    def setup_logging(self):
        """Configure production logging."""
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(self.log_file)
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure logging format
        if self.log_format == 'json':
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"module": "%(name)s", "message": "%(message)s", '
                '"filename": "%(filename)s", "line": %(lineno)d}'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        # Configure file handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, self.log_level))
        
        # Configure console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, self.log_level))
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level))
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Configure specific loggers
        logging.getLogger('uvicorn').setLevel(logging.INFO)
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        
    def get_cors_config(self):
        """Get CORS configuration for production."""
        return {
            'allow_origins': self.cors_origins,
            'allow_credentials': self.cors_allow_credentials,
            'allow_methods': self.cors_allow_methods,
            'allow_headers': self.cors_allow_headers,
        }
    
    def validate_config(self):
        """Validate production configuration."""
        required_vars = [
            'DATABASE_URL',
            'NASA_DONKI_API_KEY',
            'CORS_ORIGINS',
            'SECRET_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Validate database URL format
        if not self.database_url.startswith('postgresql://'):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        
        # Validate CORS origins
        if not self.cors_origins or self.cors_origins == ['']:
            raise ValueError("CORS_ORIGINS must be specified for production")
        
        return True


# Global production config instance
production_config = ProductionConfig()