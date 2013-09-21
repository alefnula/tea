__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '01 January 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import os
import time
import posix  # @UnresolvedImport
import signal
import logging
import tempfile
import threading
import subprocess
from tea.system import platform
from tea.process.base import Process

logger = logging.getLogger(__name__)


class PosixProcess(Process):
    def __init__(self, command, arguments=None, environment=None, redirect_output=True):
        self._commandline = self._get_cmd(command, [] if arguments is None else arguments)
        # will be created on start
        self._environment     = dict((str(key), str(value)) for key, value in environment.items()) if environment else None
        self._process         = None
        self._wait_thread     = None
        self._redirect_output = redirect_output
        self._stdout_named    = None
        self._stderr_named    = None
        self._stdout_reader   = None
        self._stderr_reader   = None

    def _get_cmd(self, command, args):
        '''Internal helper function for merging command with arguments'''
        arguments = []
        if command.endswith('.py'):
            arguments = ['python', command] + list(args)
        else:
            arguments = [command] + list(args)
        return arguments

    def start(self):
        if self._redirect_output:
            self._stdout_named    = tempfile.NamedTemporaryFile()
            self._stderr_named    = tempfile.NamedTemporaryFile()
            self._stdout_reader   = open(self._stdout_named.name, 'rb')
            self._stderr_reader   = open(self._stderr_named.name, 'rb')
            self._process = subprocess.Popen(self._commandline,
                                             stdin=subprocess.PIPE,
                                             stdout=self._stdout_named.file,
                                             stderr=self._stderr_named.file,
                                             env=self._environment)
        else:
            self._process = subprocess.Popen(self._commandline,
                                             stdin=None,
                                             stdout=open(os.devnull, 'wb'),
                                             stderr=subprocess.STDOUT,
                                             env=self._environment)
        self._wait_thread = threading.Thread(target=self._process.wait)
        self._wait_thread.setDaemon(True)
        self._wait_thread.start()

    def kill(self):
        try:
            if self._process is not None:
                self.Kill(self._process.pid)
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
                string = string + b'\n'
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

    @classmethod
    def GetProcesses(cls, sort_by_name=True, cmdline=False):
        if platform.is_a(platform.DARWIN):
            process = Process('ps', ['-eo', 'pid,comm,args' if cmdline else 'pid,comm'])
        else:
            process = Process('ps', ['h', '-eo', 'pid,comm,args' if cmdline else 'pid,comm'])
        process.start()
        process.wait()
        processes = []
        if process.exit_code == 0:
            for line in process.read().splitlines():
                if cmdline:
                    parts = line.strip().split(' ', 3)
                    try:
                        processes.append((int(parts[0]), parts[1], ' '.join(parts[2:]).strip()))
                    except ValueError:
                        logger.error('Failed to parse PID: %s' % parts[0])
                else:
                    pid, name = line.strip().split(' ', 1)
                    try:
                        processes.append((int(pid), name))
                    except ValueError:
                        logger.error('Failed to parse PID: %s' % pid)
        if sort_by_name:
            return sorted(processes, lambda t1, t2: cmp(t1[1], t2[1]) or cmp(int(t1[0]), int(t2[0])))
        else:
            return sorted(processes, lambda t1, t2: cmp(int(t1[0]), int(t2[0])) or cmp(t1[1], t2[1]))

    @classmethod
    def Find(cls, name, arg=None):
        if arg is None:
            for pid, process in cls.GetProcesses():
                # FIXME: HACK!!! Gives only the first 15 characters!!!
                if process.lower().find(name[:15].lower()) != -1 and '<defunct>' not in process.lower():
                    return process, pid
        else:
            for pid, process, cmdline in cls.GetProcesses(cmdline=True):
                # FIXME: HACK!!! Gives only the first 15 characters!!!
                if process.lower().find(name[:15].lower()) != -1:
                    if cmdline is not None and cmdline.lower().find(arg.lower()) != -1:
                        return process, pid
        return None

    @classmethod
    def Kill(cls, pid=None, process=None):
        if process is not None:
            pid = process.pid
        if pid == posix.getpgid(pid):
            os.killpg(pid, signal.SIGKILL)  # @UndefinedVariable
        else:
            os.kill(pid, signal.SIGKILL)  # @UndefinedVariable
