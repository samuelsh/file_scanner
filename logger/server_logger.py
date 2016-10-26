import logging
from logging import handlers
import os
import sys

import multiprocessing

__author__ = 'samuels'


class Logger:
    def __init__(self, output_dir=""):
        self.output_dir = output_dir
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)

        # create console handler and set level to info
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s;%(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

        # create debug file handler and set level to debug, file will rotate each 100MB
        handler = handlers.RotatingFileHandler(os.path.join(output_dir, "controller_debug.log"), "a", 100 * 1024 * 1024,
                                               10)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s;%(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

        # create debug file handler and set level to error, file will rotate each 100MB
        handler = handlers.RotatingFileHandler(os.path.join(output_dir, "controller_error.log"), "a", 100 * 1024 * 1024,
                                               10)
        handler.setLevel(logging.WARNING)
        formatter = logging.Formatter("%(asctime)s;%(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    @property
    def logger(self):
        return self._logger


class ConsoleLogger:
    def __init__(self, name):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.DEBUG)
        # create console handler and set level to info
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s;%(levelname)s - [%(name)s]: %(message)s")
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    @property
    def logger(self):
        return self._logger
