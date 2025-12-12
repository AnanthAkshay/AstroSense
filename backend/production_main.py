"""
Production entry point for AstroSense backend.
Configures production settings, logging, and monitoring.
"""

import os
import sys
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from config.production import production_config
from main import app


def setup_production_environment():
    """Set up production environment configuration."""
    try:
        # Validate configuration
        production_config.validate_config()
        
        # Setup logging
        production_config.setup_logging()
        
        logger = logging.getLogger(__name__)
        logger.info("Starting AstroSense in production mode")
        logger.info(f"Database pool size: {production_config.pool_size}")
        logger.info(f"Max overflow: {production_config.max_overflow}")
        logger.info(f"CORS origins: {production_config.cors_origins}")
        logger.info(f"API workers: {production_config.api_workers}")
        
        # Configure FastAPI app for production
        configure_production_app()
        
        return True
        
    except Exception as e:
        print(f"Failed to setup production environment: {e}")
        sys.exit(1)


def configure_production_app():
    """Configure FastAPI app for production."""
    # Update CORS middleware with production settings
    cors_config = production_config.get_cors_config()
    
    # Add production middleware if needed
    # This would be done in main.py but we can override here
    
    # Set production-specific app settings
    app.state.production_config = production_config
    app.state.database_engine = production_config.get_database_engine()
    app.state.session_factory = production_config.get_session_factory()


if __name__ == "__main__":
    # Setup production environment
    setup_production_environment()
    
    # Import uvicorn after setup
    import uvicorn
    
    # Run with production settings
    uvicorn.run(
        "production_main:app",
        host=os.getenv('API_HOST', '0.0.0.0'),
        port=int(os.getenv('API_PORT', '8000')),
        workers=production_config.api_workers,
        log_level=production_config.log_level.lower(),
        access_log=True,
        use_colors=False,
        reload=False,  # Disable reload in production
    )