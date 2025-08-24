import logging
import sys

from pythonjsonlogger.json import JsonFormatter
from .config import config


def configure_logging():
    log_handler = logging.StreamHandler(stream=sys.stdout)

    if config.LOG_JSON:
        struct_formatter = JsonFormatter(
            "{asctime}{name}{levelname}{message}{pathname}{funcName}{lineno}",
            style="{",
            rename_fields={"levelname": "level", "asctime": "time"},
        )
        log_handler.setFormatter(struct_formatter)

    logging.basicConfig(
        level=config.LOGGING_LEVEL,
        handlers=[log_handler],
    )


logger = logging.getLogger(__name__)
logger.info("HELLO")
