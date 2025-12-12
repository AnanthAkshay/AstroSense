"""Logging configuration for AstroSense"""
import logging
import os
from datetime import datetime

def setup_logger(name: str) -> logging.Logger:
    """
    Set up a logger with consistent formatting
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Get log level from environment or default to INFO
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level))
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    return logger
