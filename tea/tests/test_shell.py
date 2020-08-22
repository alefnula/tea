import unittest
from unittest import mock

from tea import shell


class TestGoto(unittest.TestCase):
    @mock.patch("tea.shell.os")
    def test_existing(self, os):
        os.getcwd.return_value = "foo"
        os.path.abspath.side_effect = lambda path: path
        os.path.isdir.return_value = True
        with shell.goto("some_directory") as ok:
            self.assertTrue(ok)
            os.getcwd.assert_called_with()
            os.path.abspath.assert_called_with("some_directory")
            os.path.isdir.assert_called_with("some_directory")
            os.chdir.assert_called_with("some_directory")
        os.chdir.assert_called_with("foo")

    @mock.patch("tea.shell.os")
    def test_non_existing_no_create(self, os):
        os.getcwd.return_value = "foo"
        os.path.abspath.side_effect = lambda path: path
        os.path.isdir.return_value = False
        with shell.goto("some_directory") as ok:
            self.assertFalse(ok)
            os.getcwd.assert_called_with()
            os.path.abspath.assert_called_with("some_directory")
            os.path.isdir.assert_called_with("some_directory")
            assert not os.chdir.called
        assert not os.chdir.called

    @mock.patch("tea.shell.os")
    def test_non_existing_create(self, os):
        os.getcwd.return_value = "foo"
        os.path.abspath.side_effect = lambda path: path
        os.path.isdir.return_value = False
        with shell.goto("some_directory", True) as ok:
            self.assertTrue(ok)
            os.getcwd.assert_called_with()
            os.path.abspath.assert_called_with("some_directory")
            os.path.isdir.assert_called_with("some_directory")
            os.makedirs.assert_called_with("some_directory", 0o755)
            os.chdir.assert_called_with("some_directory")
        os.chdir.assert_called_with("foo")

    @mock.patch("tea.shell.os")
    def test_non_existing_create_failed(self, os):
        os.getcwd.return_value = "foo"
        os.path.abspath.side_effect = lambda path: path
        os.path.isdir.return_value = False
        os.makedirs.side_effect = Exception("Failed to create")
        with shell.goto("some_directory", True) as ok:
            self.assertFalse(ok)
            os.getcwd.assert_called_with()
            os.path.abspath.assert_called_with("some_directory")
            os.path.isdir.assert_called_with("some_directory")
            os.makedirs.assert_called_with("some_directory", 0o755)
            assert not os.chdir.called
        assert not os.chdir.called

    @mock.patch("tea.shell.os")
    def test_with_throws_an_exception(self, os):
        os.getcwd.return_value = "foo"
        os.path.abspath.side_effect = lambda path: path
        os.path.isdir.return_value = True
        with self.assertRaises(Exception):
            with shell.goto("some_directory") as ok:
                self.assertTrue(ok)
                os.getcwd.assert_called_with()
                os.path.abspath.assert_called_with("some_directory")
                os.path.isdir.assert_called_with("some_directory")
                os.chdir.assert_called_with("some_directory")
                raise Exception("Failed")
        os.chdir.assert_called_with("foo")
