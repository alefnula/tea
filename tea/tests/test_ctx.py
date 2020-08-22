import unittest

from tea import ctx


class TestSuppress(unittest.TestCase):
    def test_raises_one(self):
        with ctx.suppress(IndexError):
            raise IndexError("Test")

    def test_raises_multiple(self):
        with ctx.suppress(IndexError, IOError):
            raise IndexError("Test")
        with ctx.suppress(IndexError, IOError):
            raise IOError("Test")

    def test_unexpected(self):
        with self.assertRaises(KeyError):
            with ctx.suppress(IndexError):
                raise KeyError("Test")
        with self.assertRaises(KeyError):
            with ctx.suppress(IndexError, IOError):
                raise KeyError("Test")

    def test_inheritance(self):
        with ctx.suppress(Exception):
            raise KeyError("Test")

        class MyError(KeyError):
            pass

        with ctx.suppress(KeyError):
            raise MyError("Test")
