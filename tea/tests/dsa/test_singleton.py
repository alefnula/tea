__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '05 August 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import unittest
from tea.dsa.singleton import Singleton


class TestMultiConfig(unittest.TestCase):
    def test_subclassing(self):

        class MySingleton(Singleton):
            def __init__(self, data):
                self.data = data

        first = MySingleton('First')
        second = MySingleton('Second')
        self.assertEqual(first.data, 'First')
        self.assertEqual(second.data, 'First')
        self.assertIs(first, second)
