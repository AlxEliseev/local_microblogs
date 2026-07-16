dict_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "base": {
            "format": "%(levelname)s | %(name)s | %(asctime)s | %(lineno)s | %(message)s"
        }
    },
    "handlers": {
        "file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "base",
            "filename": "logs.log",
            "maxBytes": 10458760,
            "backupCount": 5,
        },
        "stream_handler": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "base",
        },
    },
    "loggers": {
        "router_logger": {
            "level": "INFO",
            "handlers": ["stream_handler", "file_handler"],
            "propagate": False,
        },
        "crud_logger": {
            "level": "DEBUG",
            "handlers": ["stream_handler", "file_handler"],
            "propagate": False,
        },
    },
    # "filters": {},
    "root": {
        "level": "DEBUG",
        "handlers": [
            "stream_handler",
        ],
    },
}
