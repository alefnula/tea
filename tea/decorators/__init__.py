__all__ = ["combomethod", "ComboMethodError"]

import functools


class ComboMethodError(Exception):
    """Inappropriate initialization of the combo method descriptor."""

    pass


class ComboMethod(object):
    """Combo method descriptor.

    Descriptor is initializes eater by passing in the staticmethod or the
    class method. After that an instance method can be added using the instance
    decorator.

    This class should never be used. Use the ``combomethod`` function instead.
    """

    def __init__(self, staticmethod=None, classmethod=None):
        if staticmethod is None and classmethod is None:
            raise ComboMethodError(
                "Either static method or class method has to be provided"
            )
        self.staticmethod = staticmethod
        self.classmethod = classmethod
        self.instancemethod = None

    def instance(self, instancemethod):
        self.instancemethod = instancemethod
        return self

    def __get__(self, obj, type=None):
        if obj is None:
            if self.staticmethod is not None:
                return self.staticmethod
            else:

                @functools.wraps(self.classmethod)
                def wrapper(*args, **kwargs):
                    return self.classmethod(type, *args, **kwargs)

                return wrapper
        else:
            if self.instancemethod is None:
                raise ComboMethodError("Instance method is not provided")

            @functools.wraps(self.instancemethod)
            def wrapper(*args, **kwargs):
                return self.instancemethod(obj, *args, **kwargs)

            return wrapper


def combomethod(method=None, static=False):
    """Create a class method or static method.

    It will be used when you call it on the class but can be overridden by an
    instance method of the same name that will be called when the method is
    called on the instance.

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
