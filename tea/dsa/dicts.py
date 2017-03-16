__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '16 March 2017'
__copyright__ = 'Copyright (c) 2017 Viktor Kerkez'

import collections


class DictError(Exception):
    pass


class DictObject(object):
    """Dictionary with object like access.

    .. code:: python

        >>> d = DictObject({
        ...     'name': 'John Doe',
        ...     'age': 34,
        ...     'address': {
        ...         'city': 'San Francisco',
        ...         'street': 'Mission St'
        ...     }
        ...  })
        ...
        >>> d.name
        John Doe
        >>> d.address.city
        San Francisco
    """

    def __init__(self, d):
        self.__ref__ = d

    def __getattr__(self, attr):
        if attr in self.__ref__:
            value = self.__ref__[attr]
            if isinstance(value, collections.Mapping):
                return DictObject(value)
            else:
                return value
        raise AttributeError(attr)

    def __getitem__(self, item):
        if item in self.__ref__:
            value = self.__ref__[item]
            if isinstance(value, collections.Mapping):
                return DictObject(value)
            else:
                return value
        else:
            raise KeyError(item)

    def __setitem__(self, key, value):
        self.__ref__[key] = value

    def __setattr__(self, attr, value):
        if attr == '__ref__':
            object.__setattr__(self, attr, value)
        else:
            self.__ref__[attr] = value
