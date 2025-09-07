"""
Logging configuration for the Active Recall Backend
"""

import logging
import sys
from pathlib import Path
from loguru import logger
from app.core.settings import settings


def setup_logging():
    """Setup application logging configuration"""
    
    # Remove default loguru handler
    logger.remove()
    
    # Add console handler with formatting
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True
    )
    
    # Add file handler for errors
    log_dir = settings.data_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )
    
    # Add file handler for all logs
    logger.add(
        log_dir / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="50 MB",
        retention="7 days",
        compression="zip"
    )
    
    # Configure third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google.generativeai").setLevel(logging.WARNING)
    
    return logger


def get_logger(name: str = None):
    """Get a logger instance"""
    if name:
        return logger.bind(name=name)
    return logger
