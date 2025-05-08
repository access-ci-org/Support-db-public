import logging
from logging.handlers import TimedRotatingFileHandler
import os

os.makedirs(name="logs/", exist_ok=True)

logger = logging.getLogger(__name__)
logger.propagate = False
if not logger.handlers:
    FORMAT = "%(asctime)s: %(name)s: %(levelname)s: %(message)s"
    formatter = logging.Formatter(FORMAT)
    handler = TimedRotatingFileHandler(
        filename="logs/core_logic.log",
        when="D",
        interval=31,
        backupCount=24,
        atTime="midnight",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(level=logging.DEBUG)
