from __future__ import absolute_import
# Avoid shadowing the standard library json module

"""
Json Serialization helpers
==========================

This module contains custom classes and methods which help in json
serialization.
"""

__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '16 March 2017'
__copyright__ = 'Copyright (c) 2017 Viktor Kerkez'


import json


class TeaEncoder(json.JSONEncoder):
    """SBG Encoder knows how to serialize:

        1. All objects that have a custom `__json__` method
        2. Decimal numbers
        3. DateTime and Date objects
        4. BSON `ObjectId`
        5. PyMongo Cursor
    """

    to_float = frozenset(('decimal.Decimal',))
    to_str = frozenset(('bson.objectid.ObjectId',))
    to_datetime = frozenset(('datetime.datetime', 'datetime.date'))
    to_list = frozenset(('__builtin__.set', 'builtins.set',
                         'builtins.dict_keys', 'builtins.dict_values',
                         'pymongo.cursor.Cursor'))

    def __init__(self, *args, **kwargs):
        self.datetime_format = kwargs.pop('datetime_format', '%Y%m%d%H%M%S')
        super(TeaEncoder, self).__init__(*args, **kwargs)

    def default(self, o):
        try:
            return super(TeaEncoder, self).default(o)
        except TypeError:
            # First see if there is a __json__ method
            if hasattr(o, '__json__'):
                return o.__json__()
            # Then try out special classes
            cls = o.__class__
            path = '%s.%s' % (cls.__module__, cls.__name__)
            if path in self.to_float:
                return float(o)
            elif path in self.to_datetime:
                return o.strftime(self.datetime_format)
            elif path in self.to_list:
                return list(o)
            elif path in self.to_str:
                return str(o)
            raise TypeError('%s is not JSON serializable' % o)


loads = json.loads


def dumps(obj, **kw):
    """Wraps `json.dumps` using the `TeaEncoder`"""
    return json.dumps(obj, cls=TeaEncoder, **kw)
