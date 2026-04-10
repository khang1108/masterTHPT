from enum import Enum
from typing import Optional, Union
from pathlib import Path
from master.common.config import PROJECT_ROOT

import sys
import logging

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    COMPLETED = "COMPLETED"
    PROGRESS = "PROGRESS"

class ConsoleFormatter(logging.Formatter):
    """
        Clean console formatter with colors and standard level tags.
        Format: [LEVEL]   [Module]  Message
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[90m",  # Gray
        "INFO": "\033[37m",  # White
        "SUCCESS": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "PROGRESS": "\033[36m",  # Cyan
        "COMPLETE": "\033[32m",  # Green
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    def __init__(
        self,
        service_prefix: Optional[str] = None
    ):
        
        super().__init__()

        self.service_prefix = service_prefix
        
        # Check TTY status once during initialization
        stdout_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
        stderr_tty = hasattr(sys.stderr, "isatty") and sys.stderr.isatty()
        self.use_colors = stdout_tty or stderr_tty

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the record for console output.

        Args:
            record: The log record to format

        Returns:
            The formatted log message
        """
        display_level = getattr(record, "display_level", record.levelname)

        module = getattr(record, "module_name", record.name)

class Logger:
    """
    Unified logging system for MASTER.

    Features:
        - Consistent format across all modules
        - Color-coded console output
        - File logging to user/logs/
        - WebSocket streaming support
        - Success/progress/complete methods
        - Optional prefix layer prefix (Backend/Frontend/Agent)

    Usage:
        logger = Logger("my_module")   
        logger.info("Processing ...")
        logger.success("Processing completed successfully")
        logger.progress("Processing in progress...")
    """

    def __init__(
        self, 
        name: str,
        level: str = "INFO",
        console_output: bool = True,
        file_output: bool = True,
        log_dir: Optional[Union[str, Path]] = None,
        service_prefix: Optional[str] = None
    ):
        self.name = name
        self.level = level
        self.console_output = console_output
        self.file_output = file_output
        self.log_dir = log_dir
        self.service_prefix = service_prefix

        self.logger = logging.getLogger(f"masterTHPT.{name}")
        self.logger.setLevel(level)
        self.logger.handlers.clear()
        self.logger.propagate = False #! Prevent duplicate logs from root logger

        log_dir_path: Path = None
        if log_dir is None:
            pass
        else: 
            log_dir_path = Path(log_dir) if isinstance(log_dir, str) else log_dir

            if not log_dir_path.exists():
                log_dir_path.mkdir(parents=True, exist_ok=True)