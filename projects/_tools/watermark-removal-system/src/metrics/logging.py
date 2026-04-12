"""
Structured logging with JSON format and security features.

Supports component-level configuration, PII redaction, and integration with
monitoring platforms like ELK and Loki.
"""

import json
import logging
import sys
from typing import Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Try to import python-json-logger
try:
    from pythonjsonlogger import jsonlogger
    HAS_JSON_LOGGER = True
except ImportError:
    HAS_JSON_LOGGER = False
    logger.warning("python-json-logger not available, using standard formatting")


class StructuredLogger:
    """Structured logging with JSON format."""

    def __init__(
        self,
        name: str = "watermark-removal",
        level: int = logging.INFO,
        add_console_handler: bool = True,
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Clear existing handlers
        self.logger.handlers = []

        if add_console_handler:
            handler = logging.StreamHandler(sys.stdout)
            if HAS_JSON_LOGGER:
                formatter = jsonlogger.JsonFormatter()
            else:
                formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def info(self, message: str, **kwargs):
        """Log info level with structured data."""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning level with structured data."""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """Log error level with structured data."""
        self.logger.error(message, extra=kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug level with structured data."""
        self.logger.debug(message, extra=kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical level with structured data."""
        self.logger.critical(message, extra=kwargs)


class ComponentLogger:
    """Per-component logger with configurable levels."""

    def __init__(self):
        self.loggers: Dict[str, StructuredLogger] = {}
        self.component_levels: Dict[str, int] = {}

    def get_logger(self, component_name: str) -> StructuredLogger:
        """Get or create logger for component."""
        if component_name not in self.loggers:
            level = self.component_levels.get(component_name, logging.INFO)
            self.loggers[component_name] = StructuredLogger(
                name=f"watermark.{component_name}",
                level=level,
                add_console_handler=False,
            )

            # Add handler with component context
            handler = logging.StreamHandler(sys.stdout)
            if HAS_JSON_LOGGER:
                formatter = ComponentJsonFormatter(component_name)
            else:
                formatter = logging.Formatter(f"[{component_name}] %(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.loggers[component_name].logger.addHandler(handler)

        return self.loggers[component_name]

    def set_level(self, component_name: str, level: int):
        """Set log level for component."""
        self.component_levels[component_name] = level
        if component_name in self.loggers:
            self.loggers[component_name].logger.setLevel(level)


class ComponentJsonFormatter(logging.Formatter):
    """JSON formatter with component context."""

    def __init__(self, component_name: str):
        super().__init__()
        self.component_name = component_name

    def format(self, record: logging.LogRecord) -> str:
        """Format record as JSON with component context."""
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "component": self.component_name,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Add extra fields
        if hasattr(record, "extra"):
            log_obj.update(record.extra)

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


class SecureLogFormatter(logging.Formatter):
    """Log formatter with PII redaction."""

    def __init__(self, redact_pii: bool = True):
        super().__init__()
        self.redact_pii = redact_pii

    def format(self, record: logging.LogRecord) -> str:
        """Format and sanitize log record."""
        message = record.getMessage()

        if self.redact_pii:
            # Import PII redaction utilities
            try:
                from src.security.encryption import PII

                message = PII.redact_all(message)
            except ImportError:
                # Fallback if security module not available
                pass

        record.msg = message
        return super().format(record)


class ELKIntegration:
    """Integration with Elasticsearch/Logstash/Kibana stack."""

    def __init__(
        self,
        hosts: list[str] = None,
        index_name: str = "watermark-removal",
    ):
        self.hosts = hosts or ["localhost:9200"]
        self.index_name = index_name
        self.enabled = False

        # Try to import elasticsearch
        try:
            from elasticsearch import Elasticsearch

            self.es_client = Elasticsearch(self.hosts)
            self.enabled = True
            logger.info(f"ELK integration enabled: {self.hosts}")
        except ImportError:
            logger.warning("elasticsearch-py not available, ELK disabled")

    def send_log(self, log_data: Dict[str, Any]) -> bool:
        """Send log to Elasticsearch."""
        if not self.enabled:
            return False

        try:
            self.es_client.index(
                index=self.index_name,
                doc_type="_doc",
                body=log_data,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send log to ELK: {e}")
            return False


class LokiIntegration:
    """Integration with Grafana Loki."""

    def __init__(
        self,
        url: str = "http://localhost:3100",
        job_name: str = "watermark-removal",
    ):
        self.url = url
        self.job_name = job_name
        self.enabled = False

        # Try to import requests
        try:
            import requests

            self.requests = requests
            self.enabled = True
            logger.info(f"Loki integration enabled: {url}")
        except ImportError:
            logger.warning("requests not available, Loki disabled")

    def send_log(self, labels: Dict[str, str], log_line: str) -> bool:
        """Send log to Loki."""
        if not self.enabled:
            return False

        try:
            # Add default job label
            labels = {**labels, "job": self.job_name}

            # Format labels for Loki
            label_str = "{" + ", ".join(f'{k}="{v}"' for k, v in labels.items()) + "}"

            # Create push request
            url = f"{self.url}/loki/api/v1/push"
            data = {
                "streams": [
                    {
                        "stream": labels,
                        "values": [[str(int(datetime.now(timezone.utc).timestamp() * 1e9)), log_line]],
                    }
                ]
            }

            response = self.requests.post(url, json=data)
            return response.status_code == 204

        except Exception as e:
            logger.error(f"Failed to send log to Loki: {e}")
            return False


class LogConfig:
    """Configuration for logging system."""

    def __init__(self):
        self.log_level = logging.INFO
        self.component_levels: Dict[str, int] = {
            "api": logging.INFO,
            "security": logging.WARNING,
            "metrics": logging.DEBUG,
            "queue": logging.INFO,
        }
        self.enable_json = True
        self.enable_pii_redaction = True
        self.elk_enabled = False
        self.loki_enabled = False


# Global instances
component_logger = ComponentLogger()
structured_logger = StructuredLogger()
secure_formatter = SecureLogFormatter(redact_pii=True)
log_config = LogConfig()

# Optional integrations
elk_integration: Optional[ELKIntegration] = None
loki_integration: Optional[LokiIntegration] = None


def setup_elk(hosts: list[str] = None):
    """Setup ELK integration."""
    global elk_integration
    elk_integration = ELKIntegration(hosts=hosts)
    log_config.elk_enabled = True


def setup_loki(url: str = "http://localhost:3100"):
    """Setup Loki integration."""
    global loki_integration
    loki_integration = LokiIntegration(url=url)
    log_config.loki_enabled = True


def get_component_logger(name: str) -> StructuredLogger:
    """Get logger for component."""
    return component_logger.get_logger(name)


def set_component_log_level(component_name: str, level: int):
    """Set log level for component."""
    component_logger.set_level(component_name, level)
