__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '27 November 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import sys
import types
import traceback


def get_object(path='', obj=None):
    if not path:
        return obj
    if path.startswith('.'):
        if not obj:
            raise TypeError('relative imports require the "obj" argument')
    path = path.split('.')
    if obj is None:
        __import__(path[0])
        obj = sys.modules[path[0]]
        path = path[1:]
    for item in path:
        if item != '':
            if isinstance(obj, types.ModuleType):
                try:
                    __import__('%s.%s' % (obj.__name__, item))
                except:
                    pass
            obj = getattr(obj, item)
    return obj


def get_exception():
    trace = ''
    exception = ''
    exc_list = traceback.format_exception_only(sys.exc_info()[0], sys.exc_info()[1])
    for entry in exc_list:
        exception += entry
    tb_list = traceback.format_tb(sys.exc_info()[2])
    for entry in tb_list:
        trace += entry
    return '\n\n%s\n%s' % (exception, trace)
