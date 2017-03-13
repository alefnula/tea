__author__ = 'Viktor Kerkez <viktor.kerkez@gmail.com>'
__date__ = '20 January 2010'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import os
import re
import six
import sys
import time
import pytest
from tea.system import platform
from tea.process import Process, NotFound, execute, execute_and_report as er


WRITER = '''
import sys
import time

sys.{out}.write('foo')
sys.{out}.flush()
time.sleep(2)
sys.{out}.write('bar')
'''

PRINT_VAR = '''
import os

print(os.environ.get('{var}', ''))
'''


@pytest.fixture
def process():
    return Process('sleep', ['2'])


def test_start(process):
    assert not process.is_running
    process.start()
    assert process.is_running
    process.wait()
    assert not process.is_running


def test_kill(process):
    assert not process.is_running
    start = time.time()
    process.start()
    assert process.is_running
    process.kill()
    assert not process.is_running
    end = time.time()
    assert end - start < 2


def test_write():
    p = Process(sys.executable, [
        '-c', '''a = {}(); print('Said: ' + a)'''.format(
            'raw_input' if six.PY2 else 'input'
        )
    ])
    p.start()
    p.write(b'my hello text')
    p.wait()
    assert re.match('^Said: my hello text\s*$', p.read().decode('ascii'))
    assert re.match('^$', p.eread().decode('ascii'))


def test_read():
    p = Process(sys.executable, ['-c', WRITER.format(out='stdout')])
    p.start()
    if platform.is_a(platform.DOTNET):
        # TODO: .NET does not flush the outputs
        p.wait()
        assert p.read() == b'foobar'
        assert p.eread() == b''
    else:
        time.sleep(1)
        assert p.read() == b'foo'
        assert p.eread() == b''
        p.wait()
        assert p.read() == b'bar'
        assert p.eread() == b''


def test_eread():
    p = Process(sys.executable, ['-c', WRITER.format(out='stderr')])
    p.start()
    if platform.is_a(platform.DOTNET):
        # TODO: .NET does not flush the outputs
        p.wait()
        assert p.read() == b''
        assert p.eread() == b'foobar'
    else:
        time.sleep(1)
        assert p.read() == b''
        assert p.eread() == b'foo'
        p.wait()
        assert p.read() == b''
        assert p.eread() == b'bar'


def test_stdout(tmpdir):
    stdout = tmpdir.mkdir('__tests__').join('std.out')
    p = Process(sys.executable, ['-c', WRITER.format(out='stdout')],
                stdout=stdout.strpath)
    p.start()
    p.wait()
    assert p.read() == b'foobar'
    assert stdout.open('rb').read() == b'foobar'


def test_stderr(tmpdir):
    stderr = tmpdir.mkdir('__tests__').join('std.err')
    p = Process(sys.executable, ['-c', WRITER.format(out='stderr')],
                stderr=stderr.strpath)
    p.start()
    p.wait()
    assert p.eread() == b'foobar'
    assert stderr.open('rb').read() == b'foobar'


def test_environment():
    p = Process(sys.executable, ['-c', PRINT_VAR.format(var='MY_VAR')],
                env={'MY_VAR': 'My value'})
    p.start()
    p.wait()
    assert p.exit_code == 0
    assert re.match('^My value\s*$', p.read().decode('ascii'))
    assert re.match('^$', p.eread().decode('ascii'))


def test_override_environment():
    status, output, error = execute(
        sys.executable, '-c', PRINT_VAR.format(var='PATH'),
        env={'PATH': 'PATH'}
    )
    assert status == 0
    assert re.match('^PATH\s*$', output.decode('ascii'))
    assert re.match('^$', error.decode('ascii'))
    os.environ['FOO'] = 'foo'
    status, output, error = execute(
        sys.executable, '-c', PRINT_VAR.format(var='FOO')
    )
    assert status == 0
    assert re.match('^foo\s*$', output.decode('ascii'))
    assert re.match('^$', error.decode('ascii'))
    status, output, error = execute(
        sys.executable, '-c', PRINT_VAR.format(var='FOO'),
        env={'FOO': 'bar'}
    )
    assert status == 0
    assert re.match('^bar\s*$', output.decode('ascii'))
    assert re.match('^$', error.decode('ascii'))


def test_working_dir():
    working_dir = sys.exec_prefix.strip(os.pathsep)
    p = Process(sys.executable, [
        '-c', '''import os; print(os.getcwd())'''
    ], working_dir=working_dir)
    p.start()
    p.wait()
    assert p.read().decode('ascii').strip() == working_dir


def test_execute_with_error():
    status, output, error = execute(sys.executable, '-c',
                                    'import sys; sys.exit(2)')
    assert status == 2
    assert re.match('^$', output.decode('ascii'))
    assert re.match('^$', error.decode('ascii'))


def test_execute_with_success():
    status, output, error = execute('echo', 'Hello world')
    assert status == 0
    assert re.match('^Hello world\s*$', output.decode('ascii'))
    assert re.match('^$', error.decode('ascii'))


def test_execute_and_report():
    assert er(sys.executable, '-c', 'import sys; sys.exit(0)')
    assert not er(sys.executable, '-c', 'import sys; sys.exit(1)')
    assert not er(sys.executable, '-c', 'import sys; sys.exit(-1)')
    assert not er(sys.executable, '-c', 'import sys; sys.exit(2)')


def test_not_existing_command():
    pytest.raises(NotFound, lambda: execute('non_existing_command'))
