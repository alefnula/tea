__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '21 September 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import decimal
import unittest
import datetime
from tea.utils import json
from tea.utils import get_object


class Foo(object):
    def __init__(self, x, y=None):
        self.x = x
        self.y = y

    def foo(self):
        return self.x

    def __json__(self):
        return {
            'x': self.x,
            'y': self.y
        }


class TestGetObject(unittest.TestCase):
    def setUp(self):
        self.x = 42
        self.foo = Foo(self.x)

    def test_object_getter(self):
        self.assertEqual(get_object('foo', self), self.foo)
        self.assertEqual(get_object('foo.x', self), self.x)
        self.assertEqual(get_object('foo.foo', self)(), self.x)

    def test_module_getter(self):
        self.assertEqual(get_object('unittest'), unittest)
        value = get_object('subprocess')
        import subprocess
        self.assertEqual(value, subprocess)
        self.assertEqual(get_object('tea.tests.test_utils.unittest'),
                         unittest)

    def test_module_object_getter(self):
        self.assertEqual(get_object('unittest.TestCase'), unittest.TestCase)
        self.assertEqual(get_object('tea.utils.get_object'), get_object)
        self.assertEqual(get_object('tea.tests.test_utils.Foo.foo'),
                         Foo.foo)


def test_json_encode():
    d = {'a': 1, 'b': 2}

    data = json.loads(json.dumps({
        'foo': Foo(3, 4),
        'decimal': decimal.Decimal('3.0'),
        'datetime': datetime.datetime(2017, 3, 16, 18, 30, 15),
        'date': datetime.date(2017, 3, 16),
        'set': {1, 2, 3},
        'dict_keys': d.keys(),
        'dict_values': d.values(),
    }))
    assert data['foo']['x'] == 3
    assert data['foo']['y'] == 4
    assert data['decimal'] == 3.0
    assert data['datetime'] == '20170316183015'
    assert data['date'] == '20170316000000'
    assert set(data['set']) == {1, 2, 3}
    assert set(data['dict_keys']) == {'a', 'b'}
    assert set(data['dict_values']) == {1, 2}
