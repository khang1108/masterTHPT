from enum import Enum
from pathlib import Path
from typing import Optional, Union

from master.common.config import PROJECT_ROOT

import sys
import logging
import os

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    COMPLETED = "COMPLETED"
    PROGRESS = "PROGRESS"
    AGENT_NODE = "AGENT_NODE"
    TOOLS_NODE = "TOOLS_NODE"


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
        "COMPLETED": "\033[32m",  # Green
        "COMPLETE": "\033[32m",  # Green
        "AGENT_NODE": "\033[34m",  # Blue
        "TOOLS_NODE": "\033[96m",  # Light cyan
    }
    AGENT_ROLE_COLORS = {
        "parser": "\033[95m",   # Bright magenta
        "teacher": "\033[34m",  # Blue
        "verifier": "\033[32m", # Green
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def __init__(self):
        super().__init__()
        
        # Check TTY status once during initialization
        stdout_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
        stderr_tty = hasattr(sys.stderr, "isatty") and sys.stderr.isatty()
        force_color = os.getenv("FORCE_COLOR", "0") == "1"
        self.use_colors = force_color or stdout_tty or stderr_tty

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
        message = record.getMessage()

        prefix_parts: list[str] = [f"[{display_level}]", f"[{module}]"]
        prefix = " ".join(prefix_parts)

        if self.use_colors:
            color = self.COLORS.get(display_level, "")
            if display_level == LogLevel.AGENT_NODE.value:
                color = self.AGENT_ROLE_COLORS.get(str(module).lower(), color)
            if color:
                prefix = f"{self.BOLD}{color}{prefix}{self.RESET}"

        return f"{prefix} {message}"


class Logger:
    """
    Unified logging system for MASTER.

    Features:
        - Consistent format across all modules
        - Color-coded console output
        - File logging to user/logs/
        - WebSocket streaming support
        - Success/progress/complete methods
        - Lightweight, consistent prefix format

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
    ):
        self.name = name
        self.level = level
        self.console_output = console_output
        self.file_output = file_output
        self.log_dir = log_dir

        self.logger = logging.getLogger(f"masterTHPT.{name}")
        self.logger.setLevel(level)
        self.logger.handlers.clear()
        self.logger.propagate = False

        if self.console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(ConsoleFormatter())
            self.logger.addHandler(console_handler)

        if self.file_output:
            resolved_dir = self._resolve_log_dir(log_dir)
            resolved_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(resolved_dir / f"{name}.log", encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s")
            )
            self.logger.addHandler(file_handler)

    def _resolve_log_dir(self, log_dir: Optional[Union[str, Path]]) -> Path:
        if log_dir is None:
            return PROJECT_ROOT / "logs"
        return Path(log_dir) if isinstance(log_dir, str) else log_dir

    def _emit(self, level: int, message: str, display_level: Optional[str] = None):
        extra = {"module_name": self.name}
        if display_level:
            extra["display_level"] = display_level
        self.logger.log(level, message, extra=extra)

    def debug(self, message: str):
        self._emit(logging.DEBUG, message, LogLevel.DEBUG.value)

    def info(self, message: str):
        self._emit(logging.INFO, message, LogLevel.INFO.value)

    def warning(self, message: str):
        self._emit(logging.WARNING, message, LogLevel.WARNING.value)

    def error(self, message: str):
        self._emit(logging.ERROR, message, LogLevel.ERROR.value)

    def critical(self, message: str):
        self._emit(logging.CRITICAL, message, LogLevel.CRITICAL.value)

    def progress(self, message: str):
        self._emit(logging.INFO, message, LogLevel.PROGRESS.value)

    def completed(self, message: str):
        self._emit(logging.INFO, message, LogLevel.COMPLETED.value)

    def success(self, message: str):
        self.completed(message)

    def agent_node(self, message: str):
        self._emit(logging.INFO, message, LogLevel.AGENT_NODE.value)

    def tools_node(self, message: str):
        self._emit(logging.INFO, message, LogLevel.TOOLS_NODE.value)