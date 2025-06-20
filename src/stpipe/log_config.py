"""Logging setup."""

import logging
import sys
from contextlib import contextmanager

STPIPE_ROOT_LOGGER = "stpipe"
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def set_log_configuration(log_level=None, log_format=None, log_file=None):
    """
    Set a default stpipe log configuration.

    Called without arguments, this function will remove any existing
    handlers on the stpipe logger and add a new StreamHandler to log to
    STDOUT at level INFO with a default format.

    Parameters
    ----------
    log_level : int or str, optional
        A log level to set, in the parent logger and the new handlers.
        If not provided, the level is set to INFO.
    log_format : str
        A valid log format string to set in the new handlers.
    log_file : str
        A valid file path to record log messages to.

    Returns
    -------
    list of logging.Handler
        New handlers added to the stpipe root logger.
    """
    log = logging.getLogger(STPIPE_ROOT_LOGGER)

    if log_level is None:
        log_level = logging.INFO
    log.setLevel(log_level)

    # Remove any existing handlers
    for handler in log.handlers:
        log.removeHandler(handler)
        handler.close()

    # Add a stream handler
    new_handlers = [logging.StreamHandler(sys.stdout)]

    # Add a file handler
    if log_file is not None:
        new_handlers.append(logging.FileHandler(log_file))

    # Set up the log format
    if log_format is None:
        log_format = DEFAULT_FORMAT
    formatter = logging.Formatter(log_format)

    for handler in new_handlers:
        handler.setFormatter(formatter)
        handler.setLevel(log_level)
        log.addHandler(handler)

    return new_handlers


class RecordingHandler(logging.Handler):
    """
    A handler that simply accumulates LogRecord instances.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log_records = []

    @property
    def log_records(self):
        return self._log_records

    def emit(self, record):
        if self.formatter is not None:
            self._log_records.append(self.formatter.format(record))


@contextmanager
def record_logs(level=logging.NOTSET, formatter=None):
    if formatter is None:
        yield []
    else:
        handler = RecordingHandler(level=level)
        handler.setFormatter(formatter)
        logger = logging.getLogger(STPIPE_ROOT_LOGGER)
        logger.addHandler(handler)
        try:
            yield handler.log_records
        finally:
            logger.removeHandler(handler)
