__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '06 October 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'


def docstring(doc, prepend=False, join='\n'):
    """Decorator that will prepend or append a string to the current
    documentation of the target function.

    This decorator should be robust even if func.__doc__ is None
    (for example, if -OO was passed to the interpreter).

    Usage::

        @docstring('Appended this line')
        def func():
            "This docstring will have a line below."
        pass
    """
    def decorator(func):
        current = func.__doc__ if func.__doc__ else ''
        new = join.join([doc, current] if prepend else [current, doc])
        lines = len(new.strip().splitlines())
        if lines == 1:
            # If it's a one liner keep it that way and strip whitespace
            func.__doc__ = new.strip()
        else:
            # Else strip whitespace from the beginning and add a newline
            # at the end
            func.__doc__ = new.strip() + '\n'
        return func
    return decorator

