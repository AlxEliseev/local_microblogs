import logging
import sys
from .config import LOG_LEVEL


def setup_logging():
    log_format = "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s"

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )