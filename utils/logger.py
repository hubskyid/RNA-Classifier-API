"""
Logging configuration for the RNA Analysis application
"""
import logging
import logging.handlers
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from .config import config

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    console: bool = True,
    json_format: bool = None
) -> logging.Logger:
    """
    Set up a logger with file and console handlers
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Path to log file
        console: Enable console output
        json_format: Use JSON format for logs
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level or config.LOG_LEVEL))
    logger.handlers = []  # Clear existing handlers
    
    # Determine if JSON format should be used
    if json_format is None:
        json_format = config.LOG_FORMAT == "json"
    
    # Create formatters
    if json_format:
        file_formatter = JSONFormatter()
        console_formatter = JSONFormatter()
    else:
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
    
    # File handler
    if log_file:
        Path(config.LOG_DIR).mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(
            Path(config.LOG_DIR) / log_file
        )
        
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with default configuration"""
    return setup_logger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter for adding context to log messages"""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        kwargs['extra']['extra_data'] = self.extra
        return msg, kwargs


# Create default loggers
api_logger = setup_logger(
    "api",
    log_file="api.log" if not config.TESTING else None
)

gradio_logger = setup_logger(
    "gradio",
    log_file="gradio.log" if not config.TESTING else None
)

system_logger = setup_logger(
    "system",
    log_file="system.log" if not config.TESTING else None
)


def log_api_request(
    method: str,
    path: str,
    status_code: int,
    response_time: float,
    **kwargs
):
    """Log API request details"""
    api_logger.info(
        f"{method} {path} - {status_code} - {response_time:.3f}s",
        extra={'extra_data': kwargs}
    )


def log_error(
    logger: logging.Logger,
    message: str,
    exception: Optional[Exception] = None,
    **kwargs
):
    """Log error with exception details"""
    if exception:
        logger.error(
            message,
            exc_info=True,
            extra={'extra_data': kwargs}
        )
    else:
        logger.error(message, extra={'extra_data': kwargs})