__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '06 October 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import pytest
import itertools
from tea.decorators import docstring, combomethod


JOINS = ['\n', '\n\n\n', '', '---']

ONE_LINE_DOCS = [
    'Test documentation',
    ' Test documentation', 'Test Documentation ', ' Test documentation ',
    '\nTest documentation', 'Test Documentation\n', '\nTest documentation\n',
    '\n\n\nTest documentation\n\n\n',
]

MULTI_LINE_DOC = [
    'Some documentation\nthat spans\nmultiple\nlines',
    '\nSome documentation\nthat spans\nmultiple\nlines\n',
    '\n\n\nSome documentation\nthat spans\nmultiple\nlines\n\n\n',
]


@pytest.mark.parametrize('doc,join', itertools.product(ONE_LINE_DOCS, JOINS))
def test_one_line_documentation(doc, join):
    @docstring(doc)
    def func():
        pass
    assert func.__doc__ == doc.strip()

    @docstring(doc, prepend=True)
    def func():
        pass
    assert func.__doc__ == doc.strip()

    @docstring(doc, join=join)
    def func():
        """Func docs"""
        pass
    assert func.__doc__ == '\n'.join(['Func docs', join, doc.strip() + '\n'])

    @docstring(doc, prepend=True, join=join)
    def func():
        """Func docs"""
        pass
    assert func.__doc__ == '\n'.join([doc.strip(), join, 'Func docs\n'])


@pytest.mark.parametrize('doc,join', itertools.product(MULTI_LINE_DOC, JOINS))
def test_muliti_line_documentation(doc, join):
    @docstring(doc)
    def func():
        pass
    assert func.__doc__ == doc.strip() + '\n'

    @docstring(doc, prepend=True)
    def func():
        pass
    assert func.__doc__ == doc.strip() + '\n'

    @docstring(doc, join=join)
    def func():
        """Func docs"""
        pass
    assert func.__doc__ == '\n'.join(['Func docs', join, doc.strip() + '\n'])

    @docstring(doc, prepend=True, join=join)
    def func():
        """Func docs"""
        pass
    assert func.__doc__ == '\n'.join([doc.strip(), join, 'Func docs\n'])


def test_static_instance_combo():
    class Foo(object):
        def __init__(self):
            self.instance_variable = 2

        @combomethod(static=True)
        def static_and_instance(x):
            return x + 1

        @static_and_instance.instance
        def static_and_instance(self, x):
            return x + self.instance_variable

    assert Foo.static_and_instance(100) == 101
    assert Foo().static_and_instance(100) == 102


def test_class_and_instance_combo():
    class Foo(object):
        class_variable = 1

        def __init__(self):
            self.instance_variable = 2
            # Override class variable for test case
            self.class_variable = 3

        @combomethod
        def class_and_instance(cls, x):
            return x + cls.class_variable

        @class_and_instance.instance
        def class_and_instance(self, x):
            return x + self.instance_variable

    assert Foo.class_and_instance(100) == 101
    assert Foo().class_and_instance(100) == 102
