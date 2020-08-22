import unittest

from tea.dsa.singleton import Singleton


class TestMultiConfig(unittest.TestCase):
    def test_subclassing(self):
        class MySingleton(Singleton):
            def __init__(self, data):
                self.data = data

        first = MySingleton("First")
        second = MySingleton("Second")
        self.assertEqual(first.data, "First")
        self.assertEqual(second.data, "First")
        self.assertIs(first, second)
