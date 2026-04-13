# noinspection PyPackageRequirements
import contextvars  # stdlib (Python 3.7+)
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

request_id_ctx_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)

SENSITIVE_FIELD_NAMES = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "secret",
    "api_key",
}


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx_var.get("-")
        return True


def _redact_value(key: str, value: Any) -> Any:
    if key.lower() in SENSITIVE_FIELD_NAMES:
        return "***REDACTED***"

    if isinstance(value, dict):
        return {k: _redact_value(k, v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_redact_value(key, v) for v in value]

    return value


class StructuredJsonFormatter(logging.Formatter):
    STANDARD_ATTRS = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "request_id",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }

        for key, value in record.__dict__.items():
            if key not in self.STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = _redact_value(key, value)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


_configured = False


def configure_logging() -> None:
    global _configured
    if _configured:
        return

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())
    handler.addFilter(RequestIdFilter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    logging.captureWarnings(True)
    logging.getLogger("sqlalchemy.engine").setLevel(
        os.getenv("SQL_LOG_LEVEL", "WARNING").upper()
    )

    _configured = True


def set_request_id(request_id: str) -> contextvars.Token:
    return request_id_ctx_var.set(request_id)


def reset_request_id(token: contextvars.Token) -> None:
    request_id_ctx_var.reset(token)


def get_request_id() -> str:
    return request_id_ctx_var.get("-")
