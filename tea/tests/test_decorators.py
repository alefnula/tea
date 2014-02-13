__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '06 October 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import unittest
from tea.decorators import docstring


class TestDocstring(unittest.TestCase):
    def setUp(self):
        self.one_line = 'Test documentation'
        self.multi_line = '''Some documentation
that spans
multiple
lines
'''

    def test_append(self):
        @docstring(self.one_line)
        def func():
            pass
        self.assertEqual(func.__doc__, self.one_line)

        @docstring(self.one_line)
        def func():
            """Func docs"""
            pass
        self.assertEqual(func.__doc__,
                         '\n'.join(['Func docs', self.one_line + '\n']))

        @docstring(self.multi_line)
        def func():
            pass
        self.assertEqual(func.__doc__, self.multi_line)

        @docstring(self.multi_line)
        def func():
            """Func docs"""
            pass
        self.assertEqual(func.__doc__,
                         '\n'.join(['Func docs', self.multi_line]))

    def test_prepend(self):
        @docstring(self.one_line, prepend=True)
        def func():
            pass
        self.assertEqual(func.__doc__, self.one_line)

        @docstring(self.one_line, prepend=True)
        def func():
            """Func docs"""
            pass
        self.assertEqual(func.__doc__,
                         '\n'.join([self.one_line, 'Func docs\n']))

        @docstring(self.multi_line, prepend=True)
        def func():
            pass
        self.assertEqual(func.__doc__, self.multi_line)

        @docstring(self.multi_line, prepend=True)
        def func():
            """Func docs"""
            pass
        self.assertEqual(func.__doc__,
                         '\n'.join([self.multi_line, 'Func docs\n']))
