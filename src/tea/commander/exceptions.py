__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '18 January 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'


class CommandError(Exception):
    """Exception class indicating a problem while executing a command.

    If this exception is raised during the execution of a management
    command, it will be caught and turned into a nicely-printed error
    message to the appropriate output stream (i.e., stderr); as a
    result, raising this exception (with a sensible description of the
    error) is the preferred way to indicate that something has gone
    wrong in the execution of a command.
    """
    pass
