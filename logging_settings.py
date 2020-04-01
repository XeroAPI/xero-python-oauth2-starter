# -*- coding: utf-8 -*-

default_settings = {
    "version": 1,
    "formatters": {
        "default": {"format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"},
        "verbose": {
            "format": "%(asctime)s | %(levelname)s [%(name)s.%(filename)s:%(lineno)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S%z",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://flask.logging.wsgi_errors_stream",
            "formatter": "verbose",
            "level": "DEBUG",
        }
    },
    "loggers": {
        "requests_oauthlib": {"handlers": ["console"], "level": "DEBUG"},
        "xero_python": {"handlers": ["console"], "level": "DEBUG"},
        "urllib3": {"handlers": ["console"], "level": "DEBUG"},
    },
    # "root": {"level": "DEBUG", "handlers": ["console"]},
}
