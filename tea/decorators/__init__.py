__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '06 October 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

__all__ = ['docstring', 'combomethod']

import functools


def docstring(documentation, prepend=False, join=''):
    """Decorator that will prepend or append a string to the current
    documentation of the target function.

    This decorator should be robust even if ``func.__doc__`` is None
    (for example, if -OO was passed to the interpreter).

    Usage::

        @docstring('Appended this line')
        def func():
            "This docstring will have a line below."
            pass

        >>> print(func.__doc__)
        This docstring will have a line below.

        Appended this line

        >>>

    :param str documentation: Documentation string that should be added,
        appended or prepended to the current documentation string.
    :param bool prepend: Prepend the documentation string to the current
        documentation if True else append. default=False
    :param str join: String used to separate docstrings. default='\n'
    """
    def decorator(func):
        current = (func.__doc__ if func.__doc__ else '').strip()
        doc = documentation.strip()

        new = '\n'.join(
            [doc, join, current] if prepend else [current, join, doc]
        )
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


class ComboMethod(object):
    def __get__(self, obj, type=None):
        if obj is not None:
            @functools.wraps(self.instancemethod)
            def wrapper(*args, **kwargs):
                return self.instancemethod(obj, *args, **kwargs)

            return wrapper
        else:
            if self.staticmethod is not None:
                return self.staticmethod
            else:
                @functools.wraps(self.classmethod)
                def wrapper(*args, **kwargs):
                    return self.classmethod(type, *args, **kwargs)

                return wrapper

    def __init__(self, staticmethod=None, classmethod=None):
        self.staticmethod = staticmethod
        self.classmethod = classmethod

    def instance(self, instancemethod):
        self.instancemethod = instancemethod
        return self


def combomethod(method=None, static=False):
    """Creates a class method or static method that will be used when you call
    it on the class but can be overridden by an instance method of the same
    name that will be called when the method is called on the instance.

    Usage::

        class Foo(object):
            class_variable = 2

            def __init__(self):
                self.instance_variable = 3
                # Override class variable for test case
                self.class_variable = 4

            @combomethod(static=True)
            def static_and_instance(x):
                return x + 1

            @static_and_instance.instance
            def static_and_instance(self, x):
                return x + self.instance_variable

            @combomethod
            def class_and_instance(cls, x):
                return x + cls.class_variable

            @class_and_instance.instance
            def class_and_instance(self, x):
                return x + self.instance_variable

        >>> Foo.static_and_instance(100)
        101
        >>> Foo.class_and_instance(100)
        102
        >>> f = Foo()
        >>> f.static_and_instance(100)
        103
        >>> f.class_and_instance(100)
        103
    """
    return ComboMethod if static else ComboMethod(None, method)
