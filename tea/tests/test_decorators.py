import pytest
from tea.decorators import combomethod, ComboMethodError


def test_static_and_instance_method_combo():
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


def test_class_and_instance_method_combo():
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


def test_combomethod_error():
    class Foo(object):
        @combomethod
        def foo(cls):
            return 0

    assert Foo.foo() == 0
    pytest.raises(ComboMethodError, lambda: Foo().foo())

    class Bar(object):
        @combomethod(static=True)
        def bar():
            return 0

    assert Bar.bar() == 0
    pytest.raises(ComboMethodError, lambda: Bar().bar())
