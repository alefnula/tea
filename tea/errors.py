class TeaError(Exception):
    """Base class for all errors.

    This error class will be used as a base class for all other modules
    that use tea as it's base.
    """

    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return f"{self.__class__.__name__}({self.message})"

    __repr__ = __str__
