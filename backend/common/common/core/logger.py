import os
import logging
import structlog

def configure_logging():
    """
    Configure structured logging with support for log levels from environment.
    
    Reads LOG_LEVEL from environment (defaults to INFO).
    Valid levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    # Get log level from environment, default to INFO
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Map string to logging level constant
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    
    # Default to INFO if invalid level provided
    log_level = log_level_map.get(log_level_str, logging.INFO)
    
    # Configure standard library logging level
    # This is required because structlog uses stdlib.LoggerFactory
    logging.basicConfig(
        level=log_level,
        format="%(message)s",  # structlog handles formatting
    )
    
    # Set root logger level
    logging.getLogger().setLevel(log_level)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.JSONRenderer(),
        ],
        context_class=structlog.threadlocal.wrap_dict(dict),
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

