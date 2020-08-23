import unittest

from tea.utils import get_object


class Foo(object):
    def __init__(self, x, y=None):
        self.x = x
        self.y = y

    def foo(self):
        return self.x


class TestGetObject(unittest.TestCase):
    def setUp(self):
        self.x = 42
        self.foo = Foo(self.x)

    def test_object_getter(self):
        self.assertEqual(get_object("foo", self), self.foo)
        self.assertEqual(get_object("foo.x", self), self.x)
        self.assertEqual(get_object("foo.foo", self)(), self.x)

    def test_module_getter(self):
        self.assertEqual(get_object("unittest"), unittest)
        value = get_object("subprocess")
        import subprocess

        self.assertEqual(value, subprocess)
        self.assertEqual(get_object("tea.tests.test_utils.unittest"), unittest)

    def test_module_object_getter(self):
        self.assertEqual(get_object("unittest.TestCase"), unittest.TestCase)
        self.assertEqual(get_object("tea.utils.get_object"), get_object)
        self.assertEqual(get_object("tea.tests.test_utils.Foo.foo"), Foo.foo)
