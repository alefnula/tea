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
FMT_DATE = "%Y.%m.%d %H:%M:%S"

logging.basicConfig(
    stream=sys.stderr, format=FMT_SHORT, datefmt=FMT_DATE, level=logging.DEBUG
)


def configure_logging(
    filename=None,
    filemode="a",
    datefmt=FMT_DATE,
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
        datefmt (str): Use the specified date/time format.
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
        stdout_formatter = logging.Formatter(stdout_fmt, datefmt)
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
        file_formatter = logging.Formatter(fmt, datefmt)
        file_formatter.converter = time.gmtime
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        if initial_file_message:
            message = " %s " % initial_file_message
            file_handler.stream.write("\n" + message.center(100, "=") + "\n\n")
