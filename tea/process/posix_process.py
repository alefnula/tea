__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '01 January 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import io
import os
import sys
import time
import posix
import signal
import logging
import tempfile
import threading
import subprocess
from tea.utils import cmp
from tea.process import base
from tea.system import platform
from tea.decorators import docstring

logger = logging.getLogger(__name__)


@docstring(base.doc_get_processes)
def get_processes(sort_by_name=True, cmdline=False):
    if platform.is_a(platform.DARWIN):
        process = PosixProcess('ps', ['-eo', 'pid,comm,args' if cmdline
                                             else 'pid,comm'])
    else:
        process = PosixProcess('ps', ['h', '-eo', 'pid,comm,args' if cmdline
                                                  else 'pid,comm'])
    process.start()
    process.wait()
    processes = []
    if process.exit_code == 0:
        for line in process.read().splitlines():
            if cmdline:
                parts = line.strip().split(' ', 3)
                try:
                    processes.append((int(parts[0]), parts[1],
                                      ' '.join(parts[2:]).strip()))
                except ValueError:
                    logger.error('Failed to parse PID: %s' % parts[0])
            else:
                pid, name = line.strip().split(' ', 1)
                try:
                    processes.append((int(pid), name))
                except ValueError:
                    logger.error('Failed to parse PID: %s' % pid)
    if sort_by_name:
        return sorted(processes, lambda t1, t2: (cmp(t1[1], t2[1]) or
                                                 cmp(int(t1[0]), int(t2[0]))))
    else:
        return sorted(processes, lambda t1, t2: (cmp(int(t1[0]), int(t2[0])) or
                                                 cmp(t1[1], t2[1])))


@docstring(base.doc_find)
def find(name, arg=None):
    if arg is None:
        for pid, process in get_processes():
            # TODO: HACK!!! Gives only the first 15 characters!!!
            if (process.lower().find(name[:15].lower()) != -1 and
                    '<defunct>' not in process.lower()):
                return pid, process
    else:
        for pid, process, cmdline in get_processes(cmdline=True):
            # TODO: HACK!!! Gives only the first 15 characters!!!
            if process.lower().find(name[:15].lower()) != -1:
                if (cmdline is not None and
                        cmdline.lower().find(arg.lower()) != -1):
                    return pid, process
    return None


@docstring(base.doc_kill)
def kill(pid):
    if pid == posix.getpgid(pid):
        os.killpg(pid, signal.SIGKILL)
    else:
        os.kill(pid, signal.SIGKILL)


def _get_cmd(command, arguments):
    """Helper function for merging command with arguments"""
    if arguments is None:
        arguments = []
    if command.endswith('.py') or command.endswith('.pyw'):
        return [sys.executable, command] + list(arguments)
    else:
        return [command] + list(arguments)


class PosixProcess(base.Process):
    def __init__(self, command, arguments=None, env=None, stdout=None,
                 stderr=None, redirect_output=True, working_dir=None):
        self._command = command
        self._arguments = arguments
        self._commandline = _get_cmd(command, arguments)
        self._env = env
        self._process = None
        self._wait_thread = None
        self._stdout = os.path.abspath(stdout) if stdout else None
        self._stdout_reader = None
        self._stdout_writer = None
        self._stderr = os.path.abspath(stderr) if stderr else None
        self._stderr_reader = None
        self._stderr_writer = None
        self._redirect_output = (stdout or stderr or redirect_output)
        self._working_dir = working_dir

    def start(self):
        if self._redirect_output:
            if self._stdout:
                self._stdout_writer = io.open(self._stdout, 'wb')
                self._stdout_reader = io.open(self._stdout, 'rb')
            else:
                self._stdout_writer = tempfile.NamedTemporaryFile()
                self._stdout_reader = io.open(self._stdout_writer.name, 'rb')

            if self._stderr:
                self._stderr_writer = io.open(self._stderr, 'wb')
                self._stderr_reader = io.open(self._stderr, 'rb')
            else:
                self._stderr_writer = tempfile.NamedTemporaryFile()
                self._stderr_reader = io.open(self._stderr_writer.name, 'rb')
            try:
                self._process = subprocess.Popen(
                    self._commandline,
                    stdin=subprocess.PIPE,
                    stdout=(self._stdout_writer if self._stdout else
                            self._stdout_writer.file),
                    stderr=(self._stderr_writer if self._stderr else
                            self._stderr_writer.file),
                    env=self._create_env(self._env),
                    cwd=self._working_dir
                )
            except OSError:
                raise base.NotFound(
                    'Executable "{}" not found'.format(self._command)
                )
        else:
            try:
                self._process = subprocess.Popen(
                    self._commandline,
                    stdin=None,
                    stdout=io.open(os.devnull, 'wb'),
                    stderr=subprocess.STDOUT,
                    env=self._create_env(self._env),
                    cwd=self._working_dir
                )
            except OSError:
                raise base.NotFound(
                    'Executable "{}" not found'.format(self._command)
                )
        self._wait_thread = threading.Thread(target=self._process.wait)
        self._wait_thread.setDaemon(True)
        self._wait_thread.start()

    def kill(self):
        try:
            if self._process is not None:
                kill(self._process.pid)
                self._wait_thread.join()
                self._process = None
                return True
            else:
                return None
        except OSError:
            return False

    def wait(self, timeout=None):
        if timeout is not None:
            current_time = time.time()
            while time.time() - current_time < (timeout * 1000):
                if not self._process.is_running:
                    return True
                time.sleep(0.1)
            return False
        else:
            while self.is_running:
                time.sleep(0.1)
            return True

    @property
    def is_running(self):
        if self._process is None or self._process.returncode is not None:
            return False
        return True

    @property
    def pid(self):
        return self._process.pid

    @property
    def exit_code(self):
        if self.is_running:
            return None
        return self._process.returncode

    def write(self, string):
        if self._redirect_output:
            if string[-1] != b'\n':
                string += b'\n'
            self._process.stdin.write(string)
            self._process.stdin.flush()

    def read(self):
        if self._redirect_output:
            return self._stdout_reader.read()
        return ''

    def eread(self):
        if self._redirect_output:
            return self._stderr_reader.read()
        return ''
