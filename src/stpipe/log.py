"""
Logging setup etc.
"""

import io
import logging
import os
import pathlib
import sys
import warnings
from contextlib import contextmanager

from astropy.extern.configobj import validate
from astropy.extern.configobj.configobj import ConfigObj

from . import config_parser

STPIPE_ROOT_LOGGER = "stpipe"
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_CONFIGURATION = b"""
[*]
handler = stderr
level = INFO
"""

# used by cmdline "verbose"
MAX_CONFIGURATION = b"""
[*]
handler = stderr
level = DEBUG
"""


###########################################################################
# LOGS AS EXCEPTIONS


class LoggedException(Exception):  # noqa: N818
    """
    This is an exception used when a log record is converted into an
    exception.

    Use its `record` member to get the original `logging.LogRecord`.
    """

    def __init__(self, record):
        self.record = record
        Exception.__init__(self, record.getMessage())


class BreakHandler(logging.Handler):
    """
    A handler that turns logs of a certain severity or higher into
    exceptions.
    """

    _from_config = True

    def emit(self, record):
        raise LoggedException(record)


#########################################################################
# LOGGING CONFIGURATION


class LogConfig:
    """
    Stores a single logging configuration.

    Parameters
    ----------
    name : str
        The `fnmatch` pattern used to match the logging class

    handler, level, break_level, format : str
        See LogConfig.spec for a description of these values.
    """

    applied = None

    def __init__(
        self,
        handler,
        level=logging.NOTSET,
        break_level=logging.NOTSET,
        format=None,  # noqa: A002
    ):
        if isinstance(handler, str):
            handler = handler.strip().split(",")
        self.handlers = [self.get_handler(x.strip()) for x in handler]
        self.level = level
        if format is None:
            format = DEFAULT_FORMAT  # noqa: A001
        self.format = logging.Formatter(format)
        for handler in self.handlers:
            handler.setLevel(self.level)
            handler.setFormatter(self.format)

        self.break_level = break_level
        if self.break_level != logging.NOTSET:
            self.handlers.append(BreakHandler(self.break_level))

    def get_handler(self, handler_str):
        """
        Given a handler string, returns a `logging.Handler` object.
        """
        if handler_str.startswith("file:"):
            return logging.FileHandler(handler_str[5:], "w", "utf-8", True)

        if handler_str.startswith("append:"):
            return logging.FileHandler(handler_str[7:], "a", "utf-8", True)

        if handler_str == "stdout":
            return logging.StreamHandler(sys.stdout)

        if handler_str == "stderr":
            return logging.StreamHandler(sys.stderr)

        raise ValueError(f"Can't parse handler {handler_str!r}")

    def apply(self):
        """
        Applies the configuration to the root logger.
        """
        log = logging.getLogger()
        for handler in self.handlers:
            log.addHandler(handler)

        # Set the log level
        self._previous_level = log.level
        log.setLevel(self.level)
        LogConfig.applied = self

    def undo(self):
        """
        Removes the configuration from the root logger.
        """
        log = logging.getLogger()
        for handler in self.handlers:
            handler.flush()
            handler.close()
            log.removeHandler(handler)
        if LogConfig.applied is self:
            log.setLevel(self._previous_level)
            LogConfig.applied = None

    @contextmanager
    def context(self):
        """
        Context manager that applies the configuration to the root logger
        """
        self.apply()
        try:
            yield
        finally:
            self.undo()


def load_configuration(config_file):
    """
    Loads a logging configuration file.  The format of this file is
    defined in LogConfig.spec.

    Parameters
    ----------
    config_file : str, pathlib.Path instance or readable file-like object

    Returns
    -------
    LogConfig
        The configuration object or None if no valid config is found.
    """

    def _level_check(value):
        try:
            value = int(value)
        except ValueError:
            pass

        try:
            value = logging._checkLevel(value)
        except ValueError as err:
            raise validate.VdtTypeError(value) from err
        return value

    spec = config_parser.load_spec_file(LogConfig)
    if isinstance(config_file, pathlib.Path):
        config_file = str(config_file)
    config = ConfigObj(config_file, raise_errors=True, interpolation=False)
    val = validate.Validator()
    val.functions["level"] = _level_check
    config_parser.validate(config, spec, validator=val)

    for key, val in config.items():
        if key in ("", ".", "root", "*"):
            return LogConfig(**val)
        else:
            msg = "non-* log configuration never worked and will be removed"
            warnings.warn(msg, UserWarning)
    return None


def _find_logging_config_file():
    files = ["stpipe-log.cfg", "~/.stpipe-log.cfg", "/etc/stpipe-log.cfg"]

    for file in files:
        file = os.path.expanduser(file)
        if os.path.exists(file):
            return os.path.abspath(file)

    return io.BytesIO(DEFAULT_CONFIGURATION)


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
        logger = logging.getLogger()
        logger.addHandler(handler)
        try:
            yield handler.log_records
        finally:
            logger.removeHandler(handler)


logging.captureWarnings(True)
