"""
Logging module
==============
This logging module is designed as a wrapper around the python
:ref:`logging` module.

When the module is loaded it configure the logging object with some
default parameters (log to stderr with DEBUG level).
After that, user can call the L{configure_logger} function and
configure logging to file and stderr.

Usage
=====
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
... except:
...     logger.exception('Error level log entry with stack trace')
ERROR       - Error level log entry with stack trace [test:4]
Traceback (most recent call last):
  ...
Exception: Test exception
"""

__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '27 November 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

from .log import configure_logging
