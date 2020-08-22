"""Context library - providing usefull context managers."""

import contextlib


@contextlib.contextmanager
def suppress(*exceptions):
    """Ignore an exception or exception list.

    Usage::

        with suppress(OSError):
            os.remove('filename.txt')
    """
    try:
        yield
    except exceptions:
        pass
