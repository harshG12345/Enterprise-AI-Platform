"""Structured JSON logger with correlation and request-ID tracking."""

import contextvars
import json
import logging
import sys
import traceback
from datetime import UTC, datetime
from typing import Any, Dict

from app.config.settings import get_settings

settings = get_settings()

# Context variables for automatic log correlation
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id_ctx", default="system")
user_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("user_id_ctx", default=None)


class RequestIdFilter(logging.Filter):
    """Ensure every log record has request_id and user_id attributes."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id") or record.request_id == "system":
            record.request_id = request_id_ctx.get()
        if not hasattr(record, "user_id"):
            record.user_id = user_id_ctx.get()
        return True


class StructuredJSONFormatter(logging.Formatter):
    """Formats log records as structured, parseable JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "system"),
            "location": f"{record.module}:{record.funcName}:{record.lineno}",
        }

        user_id = getattr(record, "user_id", None)
        if user_id:
            log_payload["user_id"] = str(user_id)

        # Include custom extra fields if provided
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_payload["data"] = record.extra_data

        # Include exception stack trace if present
        if record.exc_info:
            log_payload["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else "Exception",
                "message": str(record.exc_info[1]),
                "stack_trace": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_payload)


def setup_logging() -> logging.Logger:
    """Initialize application logger with structured format."""
    app_logger = logging.getLogger("enterprise_ai")
    app_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    app_logger.propagate = False

    if not app_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.addFilter(RequestIdFilter())

        # Use Structured JSON formatting
        formatter = StructuredJSONFormatter()
        handler.setFormatter(formatter)
        app_logger.addHandler(handler)

    return app_logger


logger = setup_logging()
