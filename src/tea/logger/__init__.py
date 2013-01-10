__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '27 November 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

from log import *

__all__ = ['LOG_CONFIGURE',
           'LOG_VERBOSE',
           'LOG_DEBUG',
           'LOG_INFO',
           'LOG_WARNING',
           'LOG_ERROR',
           'LOG_EXCEPTION',
           'LOG_FATAL'
          ]

__doc__ = '''
Logging module
==============
This logging module is designed as a wrapper around the python I{logging}
module.

When the module is loaded it configure the logging object with some default
parameters (log to stderr with DEBUG level).
After that, user can call the L{LOG_CONFIGURE} function and configure logging
to file and stderr.

Usage
=====

>>> import tempfile
>>> from tea.logger import *
>>> LOG_CONFIGURE(filename=tempfile.mktemp())
>>> LOG_DEBUG('Debug level log entry')
>>> LOG_INFO('Info level log entry')
>>> LOG_WARNING('Warn level log entry')
WARNING     - Warn level log entry [__main__:1]
>>> LOG_ERROR('Error level log entry')
ERROR       - Error level log entry [__main__:1]
>>> LOG_FATAL('Critical level log entry')
ERROR_FATAL - Critical level log entry [__main__:1]
>>> try:
...     raise Exception('Test exception')
... except:
...     LOG_EXCEPTION('Error level log entry with stack trace')
ERROR       - Error level log entry with stack trace [__main__:4]
Traceback (most recent call last):
  ...
Exception: Test exception
'''

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
