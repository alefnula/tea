"""Logging module.

This logging module is designed as a wrapper around the python `logging`
module.

When the module is loaded it configure the logging object with some
default parameters (log to stderr with DEBUG level).
After that, user can call the L{configure_logger} function and
configure logging to file and stderr.


# Usage

>>> import logging
>>> import tempfile
>>> from tea.logger import configure_logging
>>> configure_logging(filename=tempfile.mktemp())
>>> logger = logging.getLogger('test')
>>> logger.debug('Debug level log entry')
>>> logger.info('Info level log entry')
>>> logger.warning('Warn level log entry')
WARNING     - Warn level log entry [test:1]
>>> logger.error('Error level log entry')
ERROR       - Error level log entry [test:1]
>>> logger.critical('Critical level log entry')
CRITICAL    - Critical level log entry [test:1]
>>> try:
...     raise Exception('Test exception')
... except Exception:
...     logger.exception('Error level log entry with stack trace')
ERROR       - Error level log entry with stack trace [test:4]
Traceback (most recent call last):
  ...
Exception: Test exception
"""

import os
import sys
import time
import logging
from logging.handlers import RotatingFileHandler

from tea import shell

# Constants
FMT = (
    "%(asctime)s.%(msecs)03d   %(levelname)11s: %(message)s "
    "[%(name)s:%(lineno)d]"
)
FMT_SHORT = "%(asctime)s %(levelname)11s: %(message)s [%(name)s:%(lineno)d]"
FMT_STDOUT = "%(levelname)-11s - %(message)s [%(name)s:%(lineno)d]"
FMT_TS = "%Y.%m.%d %H:%M:%S"

logging.basicConfig(
    stream=sys.stderr, format=FMT_SHORT, datefmt=FMT_TS, level=logging.DEBUG
)


def configure_logging(
    filename=None,
    filemode="a",
    ts_fmt=FMT_TS,
    fmt=FMT,
    stdout_fmt=FMT_STDOUT,
    level=logging.DEBUG,
    stdout_level=logging.WARNING,
    initial_file_message="",
    max_size=1048576,
    rotations_number=5,
    remove_handlers=True,
):
    """Configure logging module.

    Args:
        filename (str): Specifies a filename to log to.
        filemode (str): Specifies the mode to open the log file.
            Values: ``'a'``, ``'w'``. *Default:* ``a``.
        ts_fmt (str): Use the specified timestamp format.
        fmt (str): Format string for the file handler.
        stdout_fmt (str): Format string for the stdout handler.
        level (int): Log level for the file handler. Log levels are the same
            as the log levels from the standard :mod:`logging` module.
            *Default:* ``logging.DEBUG``
        stdout_level (int): Log level for the stdout handler. Log levels are
            the same as the log levels from the standard :mod:`logging` module.
            *Default:* ``logging.WARNING``
        initial_file_message (str): First log entry written in file.
        max_size (int): Maximal size of the logfile. If the size of the file
            exceed the maximal size it will be rotated.
        rotations_number (int): Number of rotations to save.
        remove_handlers (bool): Remove all existing handlers.
    """
    logger = logging.getLogger()
    logger.level = logging.NOTSET
    # Remove all handlers
    if remove_handlers:
        while len(logger.handlers) > 0:
            hdlr = logger.handlers[0]
            hdlr.close()
            logger.removeHandler(hdlr)
    # Create stdout handler
    if stdout_level is not None:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(stdout_level)
        stdout_formatter = logging.Formatter(stdout_fmt, ts_fmt)
        # stdoutFormatter.converter = time.gmtime
        stdout_handler.setFormatter(stdout_formatter)
        logger.addHandler(stdout_handler)
    # Create file handler if filename is provided
    if filename is not None:
        # Check if filename directory exists and creates it if it doesn't
        directory = os.path.abspath(os.path.dirname(filename))
        if not os.path.isdir(directory):
            shell.mkdir(directory)
        # Create file handler
        file_handler = RotatingFileHandler(
            filename, filemode, max_size, rotations_number
        )
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(fmt, ts_fmt)
        file_formatter.converter = time.gmtime
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        if initial_file_message:
            message = " %s " % initial_file_message
            file_handler.stream.write("\n" + message.center(100, "=") + "\n\n")
