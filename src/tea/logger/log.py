__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '27 November 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import os
import sys
import time
import logging

from tea.system import platform
if platform.is_only(platform.WINDOWS):
    from .win_handlers import RotatingFileHandler #@UnusedImport
else:
    from logging.handlers import RotatingFileHandler #@Reimport


# Adding custom debug levels
logging.VERBOSE = 5
logging.ERROR_FATAL = 50

logging._levelNames.update({
    5  : 'VERBOSE',
    50 : 'ERROR_FATAL',
    
    'VERBOSE'     : 5,
    'ERROR_FATAL' : 50
})

# method for custom levels
def verbose(self, msg, *args, **kwargs):
    if self.isEnabledFor(logging.VERBOSE): # @UndefinedVariable
        self._log(logging.VERBOSE, msg, args, **kwargs) # @UndefinedVariable
logging.Logger.verbose = verbose
def fatal(self, msg, *args, **kwargs):
    if self.isEnabledFor(logging.ERROR_FATAL): # @UndefinedVariable
        self._log(logging.ERROR_FATAL, msg, args, **kwargs) # @UndefinedVariable
logging.Logger.fatal = fatal



# Constants
DATE_FORMAT = '%Y.%m.%d %H:%M:%S'
FORMAT = '%(asctime)s.%(msecs)03d   %(levelname)11s: %(message)s [%(name)s:%(lineno)d]'
FORMAT_STDOUT = '%(levelname)-11s - %(message)s [%(name)s:%(lineno)d]'
FORMAT_SHORT = '%(asctime)s %(levelname)11s: %(message)s [%(name)s:%(lineno)d]'

logging.basicConfig(stream=sys.stderr, format=FORMAT_SHORT,
                    datefmt=DATE_FORMAT, level=logging.DEBUG)


def configure_logging(filename=None, filemode='a', datefmt=DATE_FORMAT,
                     format=FORMAT, stdout_format=FORMAT_STDOUT, level='DEBUG',
                     stdout_level='WARNING', initial_file_message='',
                     max_size=1048576, rotations_number=5, remove_handlers=True):
    '''Configure logging module
    
    @type  filename: string
    @param filename: Specifies a filename to log to.
    @type  filemode: char
    @param filemode: Specifies the mode to open the log file.
        Values: C{'a', 'w'}.
    @type  datefmt: string
    @param datefmt: Use the specified date/time format.
    @type  format: string
    @param format: Format string for the file handler.
    @type  stdout_format: string
    @param stdout_format: Format string for the stdout handler.
    @type  level: string
    @param level: Log level for the file handler.
        Values: C{'VERBOSE', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'ERROR_FATAL'}
    @type  stdout_level: string
    @param stdout_level: Log level for the stdout handler.
        Values: C{'VERBOSE', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'ERROR_FATAL'}
    @type  initial_file_message: string
    @param initial_file_message: First log entry written in file.
    @type  max_size: integer
    @param max_size: Maximal size of the logfile. If the size of the file exceed
        the maximal size it will be rotated.
    @type  rotations_number: integer
    @param rotations_number: Number of rotations to save
    @type  remove_handlers: boolean
    @param remove_handlers: Remove all existing handlers
    @rtype: None
    '''
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
        stdoutHandler = logging.StreamHandler(sys.stdout)
        stdoutHandler.setLevel(getattr(logging, stdout_level))
        stdoutFormatter = logging.Formatter(stdout_format, datefmt)
        #stdoutFormatter.converter = time.gmtime
        stdoutHandler.setFormatter(stdoutFormatter)
        logger.addHandler(stdoutHandler)
    # Create file handler if filename is provided
    if filename is not None:
        # Check if filename directory exists and creates it if it doesn't
        directory = os.path.abspath(os.path.dirname(filename))
        if not os.path.isdir(directory):
            os.makedirs(directory)
        # Create file handler
        fileHandler = RotatingFileHandler(filename, filemode, max_size, rotations_number)
        fileHandler.setLevel(getattr(logging, level))
        fileFormatter = logging.Formatter(format, datefmt)
        fileFormatter.converter = time.gmtime
        fileHandler.setFormatter(fileFormatter)
        logger.addHandler(fileHandler)
        if initial_file_message:
            message = ' %s ' % initial_file_message
            fileHandler.stream.write('\n' + message.center(100, '=') + '\n\n')
