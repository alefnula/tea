__author__ = 'Viktor Kerkez <viktor.kerkez@gmail.com>'
__date__ = '20 January 2010'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import os
import sys
import time
import unittest
from tea.utils import six
from tea.system import platform
from tea.process import Process, execute, execute_and_report


class TestProcess(unittest.TestCase):
    def setUp(self):
        self.command = 'sleep'
        self.args = ['2']
        self.timeout = 2
        if six.PY3:
            self.input = 'input'
        else:
            self.input = 'raw_input'

    def test_start(self):
        p = Process(self.command, self.args)
        self.assertFalse(p.is_running)
        p.start()
        self.assertTrue(p.is_running)
        p.wait()
        self.assertFalse(p.is_running)

    def test_kill(self):
        p = Process(self.command, self.args)
        self.assertFalse(p.is_running)
        start = time.time()
        p.start()
        self.assertTrue(p.is_running)
        p.kill()
        self.assertFalse(p.is_running)
        end = time.time()
        self.assertTrue(end - start < self.timeout)

    def test_write(self):
        p = Process(sys.executable,
                    ['-c', '''a = %s(); print('Said: ' + a)''' % self.input])
        p.start()
        p.write(b'my hello text')
        p.wait()
        self.assertRegexpMatches(p.read().decode('ascii'),
                                 '^Said: my hello text\s*$')
        self.assertRegexpMatches(p.eread().decode('ascii'), '^$')

    def test_read(self):
        p = Process(sys.executable, ['-c', '''import sys, time
sys.stdout.write('foo')
sys.stdout.flush()
time.sleep(2)
sys.stdout.write('bar')
'''])
        p.start()
        if platform.is_a(platform.DOTNET):
            # TODO: .NET does not flush the outputs
            p.wait()
            self.assertEqual(p.read(), b'foobar')
            self.assertEqual(p.eread(), b'')
        else:
            time.sleep(1)
            self.assertEqual(p.read(), b'foo')
            self.assertEqual(p.eread(), b'')
            p.wait()
            self.assertEqual(p.read(), b'bar')
            self.assertEqual(p.eread(), b'')

    def test_eread(self):
        p = Process(sys.executable, ['-c', '''import sys, time
sys.stderr.write('foo')
sys.stderr.flush()
time.sleep(2)
sys.stderr.write('bar')
'''])
        p.start()
        if platform.is_a(platform.DOTNET):
            # TODO: .NET does not flush the outputs
            p.wait()
            self.assertEqual(p.read(), b'')
            self.assertEqual(p.eread(), b'foobar')
        else:
            time.sleep(1)
            self.assertEqual(p.read(), b'')
            self.assertEqual(p.eread(), b'foo')
            p.wait()
            self.assertEqual(p.read(), b'')
            self.assertEqual(p.eread(), b'bar')

    def test_environment(self):
        env = {'MY_VAR': 'My value'}
        p = Process(sys.executable, ['-c', '''import os
print(os.environ.get('MY_VAR', ''))
'''], env=env)
        p.start()
        p.wait()
        self.assertEqual(p.exit_code, 0)
        self.assertRegexpMatches(p.read().decode('ascii'), '^My value\s*$')
        self.assertRegexpMatches(p.eread().decode('ascii'), '^$')

    def test_override_environment(self):
        env = {'PATH': 'PATH'}
        status, output, error = execute(sys.executable, '-c', '''import os
print(os.environ.get('PATH', ''))
''', env=env)
        self.assertEqual(status, 0)
        self.assertRegexpMatches(output.decode('ascii'), '^PATH\s*$')
        self.assertRegexpMatches(error.decode('ascii'), '^$')
        os.environ['FOO'] = 'foo'
        status, output, error = execute(sys.executable, '-c', '''import os
print(os.environ.get('FOO', ''))
''')
        self.assertEqual(status, 0)
        self.assertRegexpMatches(output.decode('ascii'), '^foo\s*$')
        self.assertRegexpMatches(error.decode('ascii'), '^$')
        status, output, error = execute(sys.executable, '-c', '''import os
print(os.environ.get('FOO', ''))
''', env={'FOO': 'bar'})
        self.assertEqual(status, 0)
        self.assertRegexpMatches(output.decode('ascii'), '^bar\s*$')
        self.assertRegexpMatches(error.decode('ascii'), '^$')

    def test_working_dir(self):
        working_dir = sys.exec_prefix.strip(os.pathsep)
        p = Process(sys.executable, [
            '-c', '''import os; print(os.getcwd())'''
        ], working_dir=working_dir)
        p.start()
        p.wait()
        self.assertEqual(p.read().decode('ascii').strip(), working_dir)


class TestWrapper(unittest.TestCase):
    def test_execute_with_error(self):
        status, output, error = execute(sys.executable, '-c',
                                        'import sys; sys.exit(2)')
        self.assertEqual(status, 2)
        self.assertRegexpMatches(output.decode('ascii'), '^$')
        self.assertRegexpMatches(error.decode('ascii'), '^$')

    def test_execute_with_success(self):
        status, output, error = execute('echo', 'Hello world')
        self.assertEqual(status, 0)
        self.assertRegexpMatches(output.decode('ascii'), '^Hello world\s*$')
        self.assertRegexpMatches(error.decode('ascii'), '^$')

    def test_execute_and_report(self):
        self.assertTrue(execute_and_report(sys.executable, '-c',
                                           'import sys; sys.exit(0)'))
        self.assertFalse(execute_and_report(sys.executable, '-c',
                                            'import sys; sys.exit(1)'))
        self.assertFalse(execute_and_report(sys.executable, '-c',
                                            'import sys; sys.exit(-1)'))
        self.assertFalse(execute_and_report(sys.executable, '-c',
                                            'import sys; sys.exit(2)'))

    def test_not_existing_command(self):
        self.assertRaises(Exception, lambda: execute('non_existing_command',
                                                     '-e', 'something'))
