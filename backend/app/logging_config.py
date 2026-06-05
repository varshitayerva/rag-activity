"""Structured logging configuration."""

import logging
import json
from datetime import datetime
import sys

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for better parsing."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

def setup_logging(level=logging.INFO):
    """Setup structured logging for the application."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(JSONFormatter())

    root_logger.addHandler(console_handler)

    # Get loggers for main modules
    loggers = {
        'backend.app': logging.getLogger('backend.app'),
        'backend.app.database': logging.getLogger('backend.app.database'),
        'backend.app.search': logging.getLogger('backend.app.search'),
        'backend.app.generation': logging.getLogger('backend.app.generation'),
    }

    return loggers

# Initialize on import
setup_logging()
