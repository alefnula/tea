__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '25 July 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import unittest
from tea.ds.config import Config, ConfigType


class TestDictConfig(unittest.TestCase):
    def setUp(self):
        self.c = Config({
            'foo': {
                'bar': {
                    'baz': 42
                },
                'baz': 43
            },
            'bar': 44,
        })
    
    def tearDown(self):
        self.c = None
    
    def test_config_format(self):
        self.assertEqual(self.c.current.fmt, ConfigType.DICT)
    
    def test_get(self, foo=True, bar=True):
        if foo:
            self.assertDictEqual(self.c.get('foo'), {'bar': {'baz': 42}, 'baz': 43})
        if bar:
            self.assertDictEqual(self.c.get('foo.bar'), {'baz': 42})
        self.assertEqual(self.c.get('foo.bar.baz'), 42)
        self.assertEqual(self.c.get('foo.baz'), 43)
        self.assertEqual(self.c.get('bar'), 44)
    
    def test_set_first_level(self):
        self.c.set('first', 45)
        self.assertEqual(self.c.get('first'), 45)
        # check the rest
        self.test_get()
    
    def test_set_second_level(self):
        self.c.set('first.second', 46)
        self.assertDictEqual(self.c.get('first'), {'second': 46})
        self.assertEqual(self.c.get('first.second'), 46)
        # check the rest
        self.test_get()

    def test_set_in_existing_first_level_one_level(self):
        self.c.set('foo.first', 47)
        self.assertDictEqual(self.c.get('foo'), {'bar': {'baz': 42}, 'baz': 43, 'first': 47})
        self.assertEqual(self.c.get('foo.first'), 47)
        # check the rest
        self.test_get(foo=False)
    
    def test_set_in_existing_first_level_two_levels(self):
        self.c.set('foo.first.second', 48)
        self.assertDictEqual(self.c.get('foo'), {'bar': {'baz': 42}, 'baz': 43, 'first': {'second': 48}})
        self.assertDictEqual(self.c.get('foo.first'), {'second': 48})
        self.assertEqual(self.c.get('foo.first.second'), 48)
        # check the rest
        self.test_get(foo=False)        
    
    def test_set_in_existing_second_level_one_level(self):
        self.c.set('foo.bar.first', 49)
        self.assertDictEqual(self.c.get('foo'), {'bar': {'baz': 42, 'first': 49}, 'baz': 43})
        self.assertDictEqual(self.c.get('foo.bar'), {'baz': 42, 'first': 49})
        self.assertEqual(self.c.get('foo.bar.first'), 49)
        # check the rest
        self.test_get(foo=False, bar=False)

    def test_set_in_existing_second_level_two_levels(self):
        self.c.set('foo.bar.first.second', 50)
        self.assertDictEqual(self.c.get('foo'), {'bar': {'baz': 42, 'first': {'second': 50}}, 'baz': 43})
        self.assertDictEqual(self.c.get('foo.bar'), {'baz': 42, 'first': {'second': 50}})
        self.assertDictEqual(self.c.get('foo.bar.first'), {'second': 50})
        self.assertEqual(self.c.get('foo.bar.first.second'), 50)
        # check the rest
        self.test_get(foo=False, bar=False)


class TestDetectJsonConfig(TestDictConfig):
    def setUp(self):
        self.c = Config(u'''
{
    "foo": {
        "bar": {
            "baz": 42
        },
        "baz": 43
    },
    "bar": 44
}
''')
    
    def test_config_format(self):
        self.assertEqual(self.c.current.fmt, ConfigType.JSON)


class TestDetectYamlConfig(TestDictConfig):
    def setUp(self):
        self.c = Config(u'''
foo:
  bar:
    baz: 42
  baz: 43
bar: 44
''')

    def test_config_format(self):
        self.assertEqual(self.c.current.fmt, ConfigType.YAML)


class TestDoubleConfig(unittest.TestCase):
    dict_first  = {'foo': {'bar': {'baz': 42}, 'baz': 43}, 'bar': 44, 'baz': 45}
    dict_second = {'foo': {'bar': {'deep': 46}, 'baz': 47, 'test': 48}, 'bar': {'baz': 49}, 'first': 50}
    
    json_first  = u'{"foo": {"bar": {"baz": 42}, "baz": 43}, "bar": 44, "baz": 45}'
    json_second = u'{"foo": {"bar": {"deep": 46}, "baz": 47, "test": 48}, "bar": {"baz": 49}, "first": 50}'
    
    yaml_first  = u'foo:\n bar:\n  baz: 42\n baz: 43\nbar: 44\nbaz: 45'
    yaml_second = u'foo:\n bar:\n  deep: 46\n baz: 47\n test: 48\nbar:\n baz: 49\nfirst: 50'
     
    def __test_structure(self, c):
        self.assertEqual(c.get('foo.bar.baz'), 42)
        self.assertEqual(c.get('foo.bar.deep'), 46)
        self.assertEqual(c.get('foo.baz'), 47)
        self.assertEqual(c.get('foo.test'), 48)
        self.assertEqual(c.get('bar.baz'), 49)
        self.assertEqual(c.get('baz'), 45)
        self.assertEqual(c.get('first'), 50)

    def test_dict_dict(self):
        c = Config(self.dict_first)
        c.attach(self.dict_second)
        self.__test_structure(c)
        self.assertEqual(c.current.fmt, ConfigType.DICT)

    def test_dict_json(self):
        c = Config(self.dict_first)
        c.attach(self.json_second)
        self.__test_structure(c)
        self.assertEqual(c.current.fmt, ConfigType.JSON)

    def test_dict_yaml(self):
        c = Config(self.dict_first)
        c.attach(self.yaml_second)
        self.__test_structure(c)
        self.assertEqual(c.current.fmt, ConfigType.YAML)

    def test_json_dict(self):
        c = Config(self.json_first)
        c.attach(self.dict_second)
        self.__test_structure(c)
        self.assertEqual(c.current.fmt, ConfigType.DICT)

    def test_json_json(self):
        c = Config(self.json_first)
        c.attach(self.json_second)
        self.__test_structure(c)
        self.assertEqual(c.current.fmt, ConfigType.JSON)

    def test_json_yaml(self):
        c = Config(self.json_first)
        c.attach(self.yaml_second)
        self.__test_structure(c)
        self.assertEqual(c.current.fmt, ConfigType.YAML)

    def test_yaml_dict(self):
        c = Config(self.yaml_first)
        c.attach(self.dict_second)
        self.__test_structure(c)
        self.assertEqual(c.current.fmt, ConfigType.DICT)

    def test_yaml_json(self):
        c = Config(self.yaml_first)
        c.attach(self.json_second)
        self.__test_structure(c)
        self.assertEqual(c.current.fmt, ConfigType.JSON)

    def test_yaml_yaml(self):
        c = Config(self.yaml_first)
        c.attach(self.yaml_second)
        self.__test_structure(c)
        self.assertEqual(c.current.fmt, ConfigType.YAML)
