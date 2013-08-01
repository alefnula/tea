__author__    = 'Viktor Kerkez <viktor.kerkez@gmail.com>'
__date__      = '20 January 2010'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import sys
import time
import unittest
from tea.process import Process, execute, execute_and_report


class TestProcess(unittest.TestCase):
    def setUp(self):
        self.command = 'sleep'
        self.timeout = '2'

    def test_start(self):
        p = Process(self.command, [self.timeout])
        self.assertFalse(p.is_running)
        p.start()
        self.assertTrue(p.is_running)
        p.wait()
        self.assertFalse(p.is_running)

    def test_kill(self):
        p = Process(self.command, [self.timeout])
        self.assertFalse(p.is_running)
        start = time.time()
        p.start()
        self.assertTrue(p.is_running)
        p.kill()
        self.assertFalse(p.is_running)
        end = time.time()
        self.assertTrue(end - start < self.timeout)

    def test_write(self):
        p = Process(sys.executable, ['-c', '''a = raw_input(); print('Said: ' + a)'''])
        p.start()
        p.write('my hello text')
        p.wait()
        self.assertRegexpMatches(p.read(), '^Said: my hello text\s+$')
        self.assertRegexpMatches(p.eread(), '^$')

    def test_read(self):
        p = Process(sys.executable, ['-c', '''import sys, time; sys.stdout.write('foo'); sys.stdout.flush(); time.sleep(2); sys.stdout.write('bar')'''])
        p.start()
        time.sleep(1)
        self.assertEqual(p.read(), 'foo')
        self.assertEqual(p.eread(), '')
        p.wait()
        self.assertEqual(p.read(), 'bar')
        self.assertEqual(p.eread(), '')

    def test_eread(self):
        p = Process(sys.executable, ['-c', '''import sys, time; sys.stderr.write('foo'); sys.stderr.flush(); time.sleep(2); sys.stderr.write('bar')'''])
        p.start()
        time.sleep(1)
        self.assertEqual(p.read(), '')
        self.assertEqual(p.eread(), 'foo')
        p.wait()
        self.assertEqual(p.read(), '')
        self.assertEqual(p.eread(), 'bar')

    def test_environment(self):
        env = {'MY_VAR': 'My value'}
        p = Process(sys.executable, ['-c', '''import os; print(os.environ.get('MY_VAR', ''))'''], environment=env)
        p.start()
        p.wait()
        self.assertEqual(p.exit_code, 0)
        self.assertRegexpMatches(p.read(), '^My value\s+$')
        self.assertRegexpMatches(p.eread(), '^$')


class TestWrapper(unittest.TestCase):
    def test_execute_with_error(self):
        status, output, error = execute(sys.executable, '-c', 'import sys; sys.exit(2)')
        self.assertEqual(status, 2)
        self.assertRegexpMatches(output, '^$')
        self.assertRegexpMatches(error, '^$')

    def test_execute_with_success(self):
        status, output, error = execute('echo', 'Hello world')
        self.assertEqual(status, 0)
        self.assertRegexpMatches(output, '^Hello world\s+$')
        self.assertRegexpMatches(error, '^$')

    def test_execute_and_report(self):
        self.assertTrue(execute_and_report(sys.executable, '-c', 'import sys; sys.exit(0)'))
        self.assertFalse(execute_and_report(sys.executable, '-c', 'import sys; sys.exit(1)'))
        self.assertFalse(execute_and_report(sys.executable, '-c', 'import sys; sys.exit(-1)'))
        self.assertFalse(execute_and_report(sys.executable, '-c', 'import sys; sys.exit(2)'))

    def test_not_existing_command(self):
        self.assertRaises(Exception, lambda: execute('non_existing_command', '-e', 'something'))
