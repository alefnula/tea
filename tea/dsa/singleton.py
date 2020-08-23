import threading


class SingletonMetaclass(type):
    """Singleton Metaclass.

    This metaclass is used for creating singletons.
    It changes the class __new__ method to maintain only one instance of the
    class, and tweaks the __init__ method to be executed only once (when the
    first instance of the class is created.

    Usage::

        >>> class MySingleton(object, metaclass=SingletonMetaclass):
        ...     '''Real singleton class.
        ...
        ...     You have to set the metaclass to SingletonMetaclass,
        ...     and define the __init__ function. Everything else will
        ...     be done by metaclass.
        ...     '''
        ...     def __init__(self, data):
        ...         print("Initializing")
        ...         self.data = data
        ...
        >>> # Only this actually happen
        >>> first = MySingleton("First initialization")
        Initializing
        >>> second = MySingleton("Second initialization") # This won't happen
        >>> first.data
        'First initialization'
        >>> second.data
        'First initialization'
    """

    def __init__(cls, *args, **kwargs):
        super(SingletonMetaclass, cls).__init__(*args, **kwargs)
        cls._instance = None
        cls._lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SingletonMetaclass, cls).__call__(
                    *args, **kwargs
                )
            return cls._instance

    @property
    def instance(cls):
        with cls._lock:
            return cls._instance


class Singleton(metaclass=SingletonMetaclass):
    """Singleton class.

    Inherit from this class if you want to have a singleton class.

    Never use SingletonMetaclass!

    Usage::

        >>> class EmptySingleton(Singleton):
        ...     '''Singleton without __init__ method'''
        ...     pass
        ...
        >>> first = EmptySingleton()
        >>> second = EmptySingleton()
        >>> assert id(first) == id(second)
        >>>
        >>> class InitSingleton(Singleton):
        ...     '''Singleton with __init__ method'''
        ...     def __init__(self, data):
        ...         print("Initializing")
        ...         self.data = data
        ...
        >>> # Only this actually happen
        >>> first = InitSingleton("First initialization")
        Initializing
        >>> second = InitSingleton("Second initialization") # This won't happen
        >>> first.data
        'First initialization'
        >>> assert first.data == second.data
    """

    pass
