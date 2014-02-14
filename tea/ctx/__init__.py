"""Context library - providing usefull context managers"""

__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '14 February 2014'
__copyright__ = 'Copyright (c) 2014 Viktor Kerkez'


import contextlib


@contextlib.contextmanager
def suppress(*exceptions):
    """Ignores an exception or exception list

    Usage::

        with suppress(OSError):
            os.remove('filename.txt')
    """
    try:
        yield
    except exceptions:
        pass
