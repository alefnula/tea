__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '25 July 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import unittest
from tea.system import platform
from tea.dsa.config import MultiConfig, Config


class TestMultiConfig(unittest.TestCase):
    dict_first = {'foo': {'bar': {'baz': 1}, 'baz': 2}, 'bar': 3, 'baz': 4}
    dict_second = {'foo': {'bar': {'deep': 5}, 'baz': 6, 'test': 7},
                   'bar': {'baz': 8}, 'first': 9}

    json_first = u'{"foo": {"bar": {"baz": 1}, "baz": 2}, "bar": 3, "baz": 4}'
    json_second = u'''{"foo": {"bar": {"deep": 5}, "baz": 6, "test": 7},
                       "bar": {"baz": 8}, "first": 9}'''

    yaml_first = u'foo:\n bar:\n  baz: 1\n baz: 2\nbar: 3\nbaz: 4'
    yaml_second = (u'foo:\n bar:\n  deep: 5\n baz: 6\n test: 7\n'
                   u'bar:\n baz: 8\nfirst: 9')

    def check_structure(self, c):
        self.assertEqual(c.get('foo.bar.baz'), 1)
        self.assertEqual(c.get('foo.bar.deep'), 5)
        self.assertEqual(c.get('foo.baz'), 6)
        self.assertEqual(c.get('foo.test'), 7)
        self.assertEqual(c.get('bar.baz'), 8)
        self.assertEqual(c.get('baz'), 4)
        self.assertEqual(c.get('first'), 9)

    def test_dict_dict(self):
        c = MultiConfig(data=self.dict_first)
        c.attach(data=self.dict_second)
        self.check_structure(c)

    def test_dict_json(self):
        c = MultiConfig(data=self.dict_first)
        c.attach(data=self.json_second, fmt=Config.JSON)
        self.check_structure(c)

    def test_dict_yaml(self):
        if platform.is_a(platform.DOTNET):
            self.skipTest('YAML is not supported on .NET')
        c = MultiConfig(data=self.dict_first)
        c.attach(data=self.yaml_second, fmt=Config.YAML)
        self.check_structure(c)

    def test_json_dict(self):
        c = MultiConfig(data=self.json_first, fmt=Config.JSON)
        c.attach(data=self.dict_second)
        self.check_structure(c)

    def test_json_json(self):
        c = MultiConfig(data=self.json_first, fmt=Config.JSON)
        c.attach(data=self.json_second, fmt=Config.JSON)
        self.check_structure(c)

    def test_json_yaml(self):
        if platform.is_a(platform.DOTNET):
            self.skipTest('YAML is not supported on .NET')
        c = MultiConfig(data=self.json_first, fmt=Config.JSON)
        c.attach(data=self.yaml_second, fmt=Config.YAML)
        self.check_structure(c)

    def test_yaml_dict(self):
        if platform.is_a(platform.DOTNET):
            self.skipTest('YAML is not supported on .NET')
        c = MultiConfig(data=self.yaml_first, fmt=Config.YAML)
        c.attach(data=self.dict_second)
        self.check_structure(c)

    def test_yaml_json(self):
        if platform.is_a(platform.DOTNET):
            self.skipTest('YAML is not supported on .NET')
        c = MultiConfig(data=self.yaml_first, fmt=Config.YAML)
        c.attach(data=self.json_second, fmt=Config.JSON)
        self.check_structure(c)

    def test_yaml_yaml(self):
        if platform.is_a(platform.DOTNET):
            self.skipTest('YAML is not supported on .NET')
        c = MultiConfig(data=self.yaml_first, fmt=Config.YAML)
        c.attach(data=self.yaml_second, fmt=Config.YAML)
        self.check_structure(c)
