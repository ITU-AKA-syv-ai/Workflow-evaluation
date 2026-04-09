import logging
from typing import Any

from pythonjsonlogger import jsonlogger

from app.config.settings import get_settings
from app.logging.context import evaluator_id_ctx


class JsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_data: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]) -> None:
        """
        Extend default JSON logging fields with additional metadata.

        Adds:
        - level: log level name
        - logger: logger name
        - evaluator_id: correlation ID from context
        - timestamp: formatted timestamp if not already present
        """
        super().add_fields(log_data, record, message_dict)

        log_data["level"] = record.levelname
        log_data["logger"] = record.name
        log_data["evaluator_id"] = evaluator_id_ctx.get()
        if not log_data.get("timestamp"):
            log_data["timestamp"] = self.formatTime(record, self.datefmt)


def setup_logging() -> None:
    log_level = get_settings().log
    handler = logging.StreamHandler()
    formatter = JsonFormatter("%(timestamp)s %(levelname)s %(logger)s %(message)s")

    # setup handler with JSON formatter
    handler.setFormatter(formatter)

    # configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.level)
    root_logger.handlers = [handler]
