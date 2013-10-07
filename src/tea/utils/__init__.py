__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '27 November 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import sys
import types
import importlib
import traceback


def get_object(path='', obj=None):
    """Returns an object from a dot path.

    Path can either be a full path, in which case the `get_object`
    function will try to import the module and follow the path. Or
    it can be a path relative to the object passed in as the second
    argument.

    Example for full paths::

        >>> get_object('os.path.join')
        <function join at 0x1002d9ed8>
        >>> get_object('tea.process')
        <module 'tea.process' from 'tea/process/__init__.pyc'>

    Example for relative paths when an object is passed in::

        >>> import os
        >>> get_object('path.join', os)
        <function join at 0x1002d9ed8>
    """
    if not path:
        return obj
    path = path.split('.')
    if obj is None:
        obj = importlib.import_module(path[0])
        path = path[1:]
    for item in path:
        if isinstance(obj, types.ModuleType):
            try:
                obj = importlib.import_module('%s.%s' % (obj.__name__, item))
            except ImportError:
                obj = getattr(obj, item)
        else:
            obj = getattr(obj, item)
    return obj


def get_exception():
    trace = ''
    exception = ''
    exc_list = traceback.format_exception_only(sys.exc_info()[0],
                                               sys.exc_info()[1])
    for entry in exc_list:
        exception += entry
    tb_list = traceback.format_tb(sys.exc_info()[2])
    for entry in tb_list:
        trace += entry
    return '\n\n%s\n%s' % (exception, trace)
