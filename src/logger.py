"""Centralized logging configuration for the ToDoList MCP server."""

import logging
import os
from pathlib import Path

def setup_logger(log_file: str = "todolist_mcp.log"):
    """Configures and returns a logger instance."""
    
    # Get the absolute path for the log file relative to the project root
    # Assuming this file is in src/, so we go up one level
    base_dir = Path(__file__).resolve().parent.parent
    log_path = base_dir / log_file

    # Create directory if it doesn't exist
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("todolist_mcp")
    
    # Prevent duplicate handlers if setup is called multiple times
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)

    # Formatter: Timestamp | Level | Module | Message
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File Handler: Stores everything
    file_handler = logging.FileHandler(str(log_path), encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Stream Handler: For console output (useful for debugging/dev)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# Initialize once at module level
logger = setup_logger()
