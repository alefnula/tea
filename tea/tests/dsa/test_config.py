__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '25 July 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import os
import six
import unittest
from tea.system import platform
from tea.dsa.config import Config
if six.PY2:
    import mock
else:
    from unittest import mock


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

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

INI_DATA = open(os.path.join(DATA_DIR, 'config.ini')).read()
JSON_DATA = open(os.path.join(DATA_DIR, 'config.json')).read()
YAML_DATA = open(os.path.join(DATA_DIR, 'config.yaml')).read()


class Checker(unittest.TestCase):
    def setUp(self):
        self.c = Config()

    def tearDown(self):
        self.c = None

    def safe_check_values(self, foo=True, bar=True):
        if foo:
            self.assertDictContainsSubset({'bar': {'baz': 1}, 'baz': 2},
                                          self.c.get('foo'))
            self.assertDictContainsSubset({'baz': 1}, self.c.get('foo.bar'))
            self.assertEqual(1, self.c.get('foo.bar.baz'))
            self.assertEqual(2, self.c.get('foo.baz'))
        if bar:
            self.assertDictContainsSubset({'baz': 3}, self.c.get('bar'))
            self.assertEqual(3, self.c.get('bar.baz'))
        self.assertEqual(4, self.c.get('baz'))

    def unsafe_check_values(self, foo=True, bar=True):
        if foo:
            self.assertDictContainsSubset({'bar': {'baz': 1}, 'baz': 2},
                                          self.c['foo'])
            self.assertDictContainsSubset({'baz': 1}, self.c['foo.bar'])
            self.assertEqual(1, self.c['foo.bar.baz'])
            self.assertEqual(2, self.c['foo.baz'])
        if bar:
            self.assertDictContainsSubset({'baz': 3}, self.c['bar'])
            self.assertEqual(3, self.c['bar.baz'])
        self.assertEqual(4, self.c['baz'])


class TestConfigCreation(Checker):
    def test_data_dict(self):
        self.c = Config(data=DICT_DATA)
        self.safe_check_values()

    def test_data_json(self):
        self.c = Config(data=JSON_DATA, fmt=Config.JSON)
        self.safe_check_values()

    def test_data_yaml(self):
        if platform.is_a(platform.DOTNET):
            self.skipTest('YAML is not supported on .NET')
        self.c = Config(data=YAML_DATA, fmt=Config.YAML)
        self.safe_check_values()

    def test_file_json(self):
        self.c = Config(filename=os.path.join(DATA_DIR, 'config.json'))
        self.safe_check_values()

    def test_file_yaml(self):
        self.c = Config(filename=os.path.join(DATA_DIR, 'config.yaml'))
        self.safe_check_values()

    def test_non_existing_file(self):
        self.c = Config(filename=os.path.join(DATA_DIR, 'non_existin.yaml'))
        self.assertEqual(self.c.data, {})

    def test_unsupported_format(self):
        self.c = Config(filename=os.path.join(DATA_DIR, 'config.ini'))
        self.assertEqual(self.c.data, {})
        self.c = Config(data=INI_DATA, fmt='INI')
        self.assertEqual(self.c.data, {})

    def test_invalid_format(self):
        self.c = Config(filename=os.path.join(DATA_DIR, 'config.ini'),
                        fmt=Config.YAML)
        self.assertEqual(self.c.data, {})
        self.c = Config(data=INI_DATA, fmt=Config.YAML)
        self.assertEqual(self.c.data, {})

    @mock.patch('os.path.isdir', return_value=False)
    @mock.patch('os.makedirs')
    @mock.patch('io.open')
    def test_save_json(self, io_open, makedirs, isdir):
        filename = 'some_filename'
        dirname = os.path.abspath(os.path.dirname(filename))
        c = Config(data=JSON_DATA, fmt=Config.JSON)
        c.filename = filename
        c.save()
        isdir.assert_called_with(dirname)
        makedirs.assert_called_with(dirname, 0o755)
        io_open.assert_called_with(filename, 'w', encoding='utf-8')
        io_open.result.write.asswert_called_with(JSON_DATA)

    @mock.patch('os.path.isdir', return_value=False)
    @mock.patch('os.makedirs')
    @mock.patch('io.open')
    def test_save_yaml(self, io_open, makedirs, isdir):
        filename = 'some_filename'
        dirname = os.path.abspath(os.path.dirname(filename))
        c = Config(data=YAML_DATA, fmt=Config.YAML)
        c.filename = filename
        c.save()
        isdir.assert_called_with(dirname)
        makedirs.assert_called_with(dirname, 0o755)
        io_open.assert_called_with(filename, 'w', encoding='utf-8')
        io_open.result.write.asswert_called_with(YAML_DATA)

    @mock.patch('os.path.isdir')
    @mock.patch('os.makedirs')
    @mock.patch('io.open')
    def test_save_unsupported(self, io_open, makedirs, isdir):
        isdir.return_value = True
        filename = 'some_filename'
        dirname = os.path.abspath(os.path.dirname(filename))
        c = Config(data=YAML_DATA, fmt=Config.YAML)
        c.filename = filename
        c.fmt = 'INI'
        c.save()
        isdir.assert_called_with(dirname)
        assert not makedirs.called
        assert not io_open.called


class TestSafeConfigAddition(Checker):
    def setUp(self):
        self.c = Config(data=DICT_DATA)

    def test_add_first_level(self):
        self.c.set('first', 5)
        self.assertEqual(self.c.get('first'), 5)
        # the rest should be untouched
        self.safe_check_values()

    def test_add_second_level(self):
        self.c.set('first.second', 6)
        self.assertDictEqual(self.c.get('first'), {'second': 6})
        self.assertEqual(self.c.get('first.second'), 6)
        # the rest should be untouched
        self.safe_check_values()

    def test_add_in_existing_first_level_one_level(self):
        self.c.set('foo.first', 7)
        self.assertEqual(self.c.get('foo.first'), 7)
        # the rest should be untouched
        self.safe_check_values()

    def test_add_in_existing_first_level_two_levels(self):
        self.c.set('foo.first.second', 8)
        self.assertDictEqual(self.c.get('foo.first'), {'second': 8})
        self.assertEqual(self.c.get('foo.first.second'), 8)
        # the rest should be untouched
        self.safe_check_values()

    def test_add_in_existing_second_level_one_level(self):
        self.c.set('foo.bar.first', 9)
        self.assertDictEqual(self.c.get('foo'),
                             {'bar': {'baz': 1, 'first': 9}, 'baz': 2})
        self.assertDictEqual(self.c.get('foo.bar'), {'baz': 1, 'first': 9})
        self.assertEqual(self.c.get('foo.bar.first'), 9)
        # the rest should be untouched
        self.safe_check_values(foo=False)

    def test_add_in_existing_second_level_two_levels(self):
        self.c.set('foo.bar.first.second', 10)
        self.assertDictEqual(self.c.get('foo'),
                             {'bar': {'baz': 1, 'first': {'second': 10}},
                              'baz': 2})
        self.assertDictEqual(self.c.get('foo.bar'),
                             {'baz': 1, 'first': {'second': 10}})
        self.assertDictEqual(self.c.get('foo.bar.first'), {'second': 10})
        self.assertEqual(self.c.get('foo.bar.first.second'), 10)
        # the rest should be untouched
        self.safe_check_values(foo=False)

    def test_list_insertion(self):
        self.c.set('foo.l', [])
        self.assertEqual(self.c.get('foo.l'), [])
        self.c.insert('foo.l', 1)
        self.assertEqual(self.c.get('foo.l'), [1])
        self.assertEqual(self.c.get('foo.l.0'), 1)
        self.c.insert('foo.l', 0, 0)
        self.assertEqual(self.c.get('foo.l'), [0, 1])
        self.assertEqual(self.c.get('foo.l.0'), 0)
        self.assertEqual(self.c.get('foo.l.1'), 1)
        self.c.set('foo.l.0', 2)
        self.assertEqual(self.c.get('foo.l'), [2, 1])
        self.assertEqual(self.c.get('foo.l.0'), 2)
        self.assertEqual(self.c.get('foo.l.1'), 1)

    def test_insertion_in_non_list(self):
        with self.assertRaises(KeyError):
            self.c.insert('foo', 0)


class TestSafeConfigSetting(Checker):
    def setUp(self):
        self.c = Config(data=DICT_DATA)

    def test_set_first_level(self):
        self.c.set('foo', 11)
        self.assertEqual(self.c.get('foo'), 11)
        # the rest should be untouched
        self.safe_check_values(foo=False)

    def test_set_second_level(self):
        self.c.set('foo.bar', 12)
        self.assertDictEqual(self.c.get('foo'), {'bar': 12, 'baz': 2})
        self.assertEqual(self.c.get('foo.bar'), 12)
        # the rest should be untouched
        self.safe_check_values(foo=False)

    def test_set_third_level(self):
        self.c.set('foo.bar.baz', 13)
        self.assertDictEqual(self.c.get('foo'), {'bar': {'baz': 13}, 'baz': 2})
        self.assertDictEqual(self.c.get('foo.bar'), {'baz': 13})
        self.assertEqual(self.c.get('foo.bar.baz'), 13)
        # the rest should be untouched
        self.safe_check_values(foo=False)


class TestSafeConfigDeleting(Checker):
    def setUp(self):
        self.c = Config(data=DICT_DATA)

    def test_delete_first_level(self):
        self.c.delete('foo')
        self.assertEqual(self.c.get('foo'), None)
        # the rest should be untouched
        self.safe_check_values(foo=False)

    def test_delete_second_level(self):
        self.c.delete('foo.bar')
        self.assertDictEqual(self.c.get('foo'), {'baz': 2})
        self.assertEqual(self.c.get('foo.bar'), None)
        # the rest should be untouched
        self.safe_check_values(foo=False)

    def test_delete_third_level(self):
        self.c.delete('foo.bar.baz')
        self.assertDictEqual(self.c.get('foo'), {'bar': {}, 'baz': 2})
        self.assertDictEqual(self.c.get('foo.bar'), {})
        self.assertEqual(self.c.get('foo.bar.baz'), None)
        # the rest should be untouched
        self.safe_check_values(foo=False)

    def test_delete_from_list(self):
        self.c.set('foo.l', [1, 2, 3])
        self.c.delete('foo.l.1')
        self.assertEqual(self.c.get('foo.l'), [1, 3])
        del self.c['foo.l.0']
        self.assertEqual(self.c.get('foo.l'), [3])

    def test_safe_delete(self):
        self.c.delete('non_existent')
        self.safe_check_values()


class TestUnsafeConfigGetting(Checker):
    def setUp(self):
        self.c = Config(data=DICT_DATA)

    def tearDown(self):
        self.c = None

    def test_unsafe_get(self):
        self.unsafe_check_values()

    def test_unsafe_key_error(self):
        self.assertRaises(KeyError, lambda: self.c['nonexistant'])
        self.assertRaises(KeyError, lambda: self.c['non.existant'])
        self.assertRaises(KeyError, lambda: self.c['foo.nonexistant'])
        self.assertRaises(KeyError, lambda: self.c['foo.non.existant'])
        self.assertRaises(KeyError, lambda: self.c['foo.bar.nonexistant'])
        self.assertRaises(KeyError, lambda: self.c['foo.bar.non.existant'])
        self.assertRaises(KeyError, lambda: self.c['foo.bar.baz.nonexistant'])
        self.assertRaises(KeyError, lambda: self.c['foo.bar.baz.non.existant'])

    def test_unsafe_index_error(self):
        self.c['list'] = [1, 2]
        self.assertEqual(self.c['list.0'], 1)
        self.assertEqual(self.c['list.1'], 2)
        self.assertEqual(self.c['list.-1'], 2)
        self.assertEqual(self.c['list.-2'], 1)
        self.assertRaises(IndexError, lambda: self.c['list.2'])
        self.assertRaises(IndexError, lambda: self.c['list.-3'])

    def test_keys(self):
        self.assertEqual(self.c.keys(), set(['foo', 'bar', 'baz']))

    def test_contains(self):
        # Existing
        self.assertTrue('foo' in self.c)
        self.assertTrue('foo.bar' in self.c)
        self.assertTrue('foo.bar.baz' in self.c)
        self.assertTrue('foo.baz' in self.c)
        self.assertTrue('bar' in self.c)
        self.assertTrue('bar.baz' in self.c)
        self.assertTrue('baz' in self.c)
        # Non existing
        self.assertFalse('oof' in self.c)
        self.assertFalse('bar.foo' in self.c)
        self.assertFalse('baz.foo' in self.c)
        self.assertFalse('baz.bar' in self.c)
        self.assertFalse('foo.baz.bar' in self.c)
