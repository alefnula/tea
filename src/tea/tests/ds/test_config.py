__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '25 July 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import unittest
from tea.ds.config import Config

DICT_DATA = {
    'foo': {
        'bar': {
            'baz': 1
        },
        'baz': 2
    },
    'bar': {
        'baz': 3
    },
    'baz': 4
}

JSON_DATA = '''
{
    "foo": {
        "bar": {
            "baz": 1
        },
        "baz": 2
    },
    "bar": {
        "baz": 3
    },
    "baz": 4
}
'''

YAML_DATA = '''
foo:
  bar:
    baz: 1
  baz: 2
bar:
  baz: 3
baz: 4
'''

class Checker(unittest.TestCase):
    def setUp(self):
        self.c = Config()
    
    def tearDown(self):
        self.c = None
    
    def check_values(self, foo=True, bar=True):
        if foo:
            self.assertDictContainsSubset({'bar': {'baz': 1}, 'baz': 2}, self.c.get('foo'))
            self.assertDictContainsSubset({'baz': 1}, self.c.get('foo.bar'))
            self.assertEqual(1, self.c.get('foo.bar.baz'))
            self.assertEqual(2, self.c.get('foo.baz'))
        if bar:
            self.assertDictContainsSubset({'baz': 3}, self.c.get('bar'))
            self.assertEqual(3, self.c.get('bar.baz'))
        self.assertEqual(4, self.c.get('baz'))


class TestConfigCreation(Checker):
    def test_data_dict(self):
        self.c = Config(data=DICT_DATA)
        self.check_values()
    
    def test_data_json(self):
        self.c = Config(data=JSON_DATA, fmt=Config.JSON)
        self.check_values()
    
    def test_data_yaml(self):
        self.c = Config(data=YAML_DATA, fmt=Config.YAML)
        self.check_values()


class TestConfigAddition(Checker):
    def setUp(self):
        self.c = Config(data=DICT_DATA)

    def test_add_first_level(self):
        self.c.set('first', 5)
        self.assertEqual(self.c.get('first'), 5)
        # the rest should be untouched
        self.check_values()
     
    def test_add_second_level(self):
        self.c.set('first.second', 6)
        self.assertDictEqual(self.c.get('first'), {'second': 6})
        self.assertEqual(self.c.get('first.second'), 6)
        # the rest should be untouched
        self.check_values()
 
    def test_add_in_existing_first_level_one_level(self):
        self.c.set('foo.first', 7)
        self.assertEqual(self.c.get('foo.first'), 7)
        # the rest should be untouched
        self.check_values()
     
    def test_add_in_existing_first_level_two_levels(self):
        self.c.set('foo.first.second', 8)
        self.assertDictEqual(self.c.get('foo.first'), {'second': 8})
        self.assertEqual(self.c.get('foo.first.second'), 8)
        # the rest should be untouched
        self.check_values()      

    def test_add_in_existing_second_level_one_level(self):
        self.c.set('foo.bar.first', 9)
        self.assertDictEqual(self.c.get('foo'), {'bar': {'baz': 1, 'first': 9}, 'baz': 2})
        self.assertDictEqual(self.c.get('foo.bar'), {'baz': 1, 'first': 9})
        self.assertEqual(self.c.get('foo.bar.first'), 9)
        # the rest should be untouched
        self.check_values(foo=False)
 
    def test_add_in_existing_second_level_two_levels(self):
        self.c.set('foo.bar.first.second', 10)
        self.assertDictEqual(self.c.get('foo'), {'bar': {'baz': 1, 'first': {'second': 10}}, 'baz': 2})
        self.assertDictEqual(self.c.get('foo.bar'), {'baz': 1, 'first': {'second': 10}})
        self.assertDictEqual(self.c.get('foo.bar.first'), {'second': 10})
        self.assertEqual(self.c.get('foo.bar.first.second'), 10)
        # the rest should be untouched
        self.check_values(foo=False)


class TestConfigSetting(Checker):
    def setUp(self):
        self.c = Config(data=DICT_DATA)
    
    def test_set_first_level(self):
        self.c.set('foo', 11)
        self.assertEqual(self.c.get('foo'), 11)
        # the rest should be untouched
        self.check_values(foo=False)

    def test_set_second_level(self):
        self.c.set('foo.bar', 12)
        self.assertDictEqual(self.c.get('foo'), {'bar': 12, 'baz': 2})
        self.assertEqual(self.c.get('foo.bar'), 12)
        # the rest should be untouched
        self.check_values(foo=False)

    def test_set_third_level(self):
        self.c.set('foo.bar.baz', 13)
        self.assertDictEqual(self.c.get('foo'), {'bar': {'baz': 13}, 'baz': 2})
        self.assertDictEqual(self.c.get('foo.bar'), {'baz': 13})
        self.assertEqual(self.c.get('foo.bar.baz'), 13)
        # the rest should be untouched
        self.check_values(foo=False)


class TestConfigDeleting(Checker):
    def setUp(self):
        self.c = Config(data=DICT_DATA)
    
    def test_delete_first_level(self):
        self.c.delete('foo')
        self.assertEqual(self.c.get('foo'), None)
        # the rest should be untouched
        self.check_values(foo=False)

    def test_delete_second_level(self):
        self.c.delete('foo.bar')
        self.assertDictEqual(self.c.get('foo'), {'baz': 2})
        self.assertEqual(self.c.get('foo.bar'), None)
        # the rest should be untouched
        self.check_values(foo=False)

    def test_delete_third_level(self):
        self.c.delete('foo.bar.baz')
        self.assertDictEqual(self.c.get('foo'), {'bar': {}, 'baz': 2})
        self.assertDictEqual(self.c.get('foo.bar'), {})
        self.assertEqual(self.c.get('foo.bar.baz'), None)
        # the rest should be untouched
        self.check_values(foo=False)
