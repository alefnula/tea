__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '27 November 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import os
import sys
import time
import logging

from tea.system import platform
if platform.is_only(platform.WINDOWS):
    from .win_handlers import RotatingFileHandler  # @UnusedImport
else:
    from logging.handlers import RotatingFileHandler  # @Reimport

# Constants
FMT = ('%(asctime)s.%(msecs)03d   %(levelname)11s: %(message)s '
       '[%(name)s:%(lineno)d]')
FMT_SHORT = '%(asctime)s %(levelname)11s: %(message)s [%(name)s:%(lineno)d]'
FMT_STDOUT = '%(levelname)-11s - %(message)s [%(name)s:%(lineno)d]'
FMT_DATE = '%Y.%m.%d %H:%M:%S'

logging.basicConfig(stream=sys.stderr, format=FMT_SHORT,
                    datefmt=FMT_DATE, level=logging.DEBUG)


def configure_logging(filename=None, filemode='a', datefmt=FMT_DATE,
                      fmt=FMT, stdout_fmt=FMT_STDOUT, level=logging.DEBUG,
                      stdout_level=logging.WARNING, initial_file_message='',
                      max_size=1048576, rotations_number=5,
                      remove_handlers=True):
    """Configure logging module.

    :param str filename: Specifies a filename to log to.
    :param str filemode: Specifies the mode to open the log file. Values:
                         ``'a'``, ``'w'``. *Default:* ``a``
    :param str datefmt: Use the specified date/time format.
    :param str fmt: Format string for the file handler.
    :param str stdout_fmt: Format string for the stdout handler.
    :param int level: Log level for the file handler. Log levels are the same
                      as the log levels from the standard :mod:`logging`
                      module. *Default:* ``logging.DEBUG``
    :param int stdout_level: Log level for the stdout handler. Log levels are
                             the same as the log levels from the standard
                             :mod:`logging` module. *Default:*
                             ``logging.WARNING``
    :param str initial_file_message: First log entry written in file.
    :param int max_size: Maximal size of the logfile. If the size of the file
                         exceed the maximal size it will be rotated.
    :param int rotations_number: Number of rotations to save
    :param bool remove_handlers: Remove all existing handlers
    :rtype: None
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
        #stdoutFormatter.converter = time.gmtime
        stdout_handler.setFormatter(stdout_formatter)
        logger.addHandler(stdout_handler)
    # Create file handler if filename is provided
    if filename is not None:
        # Check if filename directory exists and creates it if it doesn't
        directory = os.path.abspath(os.path.dirname(filename))
        if not os.path.isdir(directory):
            os.makedirs(directory)
        # Create file handler
        file_handler = RotatingFileHandler(filename, filemode, max_size,
                                           rotations_number)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(fmt, datefmt)
        file_formatter.converter = time.gmtime
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        if initial_file_message:
            message = ' %s ' % initial_file_message
            file_handler.stream.write('\n' + message.center(100, '=') + '\n\n')
