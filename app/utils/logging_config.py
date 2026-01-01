"""
Enhanced logging configuration using Rich
"""
import logging
import sys
from rich.logging import RichHandler
from rich.console import Console
from rich.traceback import install
from app.config import settings

# Install rich traceback for better error formatting
install(show_locals=True)

# Create console for rich output
console = Console()


def setup_logging():
    """Setup rich logging configuration"""
    # Get log level from settings or default to INFO
    log_level = logging.DEBUG if settings.debug else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                show_path=settings.debug,
                tracebacks_show_locals=settings.debug,
                markup=True,
                show_time=True,
                show_level=True,
            )
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    
    # Get logger for this module
    logger = logging.getLogger(__name__)
    logger.info(f"[bold green]✓[/bold green] Logging configured (Level: {logging.getLevelName(log_level)})")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)

