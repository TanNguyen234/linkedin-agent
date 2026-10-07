"""Sanitized structured logging for LinkedIn Agent Suite.

Never logs passwords, session cookies, auth tokens, or private credentials.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from rich.console import Console
from rich.logging import RichHandler

from .config import get_settings

console = Console()

# Patterns to scrub from logs
_SECRET_PATTERNS = [
    re.compile(r"li_at=[a-zA-Z0-9_\-]+", re.IGNORECASE),
    re.compile(r"JSESSIONID=[a-zA-Z0-9_\-]+", re.IGNORECASE),
    re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]+", re.IGNORECASE),
    re.compile(r"password['\"]?\s*[:=]\s*['\"]?[^\s,'\"]+", re.IGNORECASE),
    re.compile(r"token['\"]?\s*[:=]\s*['\"]?[^\s,'\"]+", re.IGNORECASE),
]


class SanitizingFilter(logging.Filter):
    """Filter that strips cookies, tokens, and credentials from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.sanitize(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.sanitize(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(self.sanitize(str(arg)) for arg in record.args)
        return True

    @staticmethod
    def sanitize(text: str) -> str:
        for pattern in _SECRET_PATTERNS:
            text = pattern.sub("[REDACTED]", text)
        return text


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure structured, sanitized file and console logging."""
    settings = get_settings()
    log_file = settings.logs_dir / f"agent_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"

    root_logger = logging.getLogger("linkedin_agent_suite")
    root_logger.setLevel(level)

    # Avoid duplicate handlers
    if not root_logger.handlers:
        sanitizer = SanitizingFilter()

        # Rich console handler
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
        )
        console_handler.setLevel(level)
        console_handler.addFilter(sanitizer)
        root_logger.addHandler(console_handler)

        # File handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(level)
        file_handler.addFilter(sanitizer)
        root_logger.addHandler(file_handler)

    return root_logger


def log_action(
    logger: logging.Logger,
    workflow: str,
    action: str,
    target: str,
    status: str,
    duration: float | None = None,
    error: str | None = None,
) -> None:
    """Structured action audit helper."""
    dur_str = f" duration={duration:.2f}s" if duration is not None else ""
    err_str = f" error=\"{error}\"" if error else ""
    msg = f"workflow={workflow} action={action} target={target} status={status}{dur_str}{err_str}"
    if status == "SUCCESS":
        logger.info(msg)
    elif status in ("FAILED", "BLOCKED"):
        logger.error(msg)
    else:
        logger.warning(msg)
