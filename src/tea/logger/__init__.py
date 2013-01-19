__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '27 November 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

from log import configure_logging

__doc__ = '''
Logging module
==============
This logging module is designed as a wrapper around the python I{logging}
module.

When the module is loaded it configure the logging object with some default
parameters (log to stderr with DEBUG level).
After that, user can call the L{configure_logger} function and configure logging
to file and stderr.

Usage
=====

>>> import tempfile
>>> from tea.logger import configure_logger
>>> configure_logger(filename=tempfile.mktemp())
>>> logging.debug('Debug level log entry')
>>> logging.info('Info level log entry')
>>> logging.warning('Warn level log entry')
WARNING     - Warn level log entry [__main__:1]
>>> logging.error('Error level log entry')
ERROR       - Error level log entry [__main__:1]
>>> logging.fatal('Critical level log entry')
ERROR_FATAL - Critical level log entry [__main__:1]
>>> try:
...     raise Exception('Test exception')
... except:
...     logging.exception('Error level log entry with stack trace')
ERROR       - Error level log entry with stack trace [__main__:4]
Traceback (most recent call last):
  ...
Exception: Test exception
'''

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
