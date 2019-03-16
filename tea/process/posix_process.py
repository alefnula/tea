__author__ = "Viktor Kerkez <alefnula@gmail.com>"
__date__ = "01 January 2009"
__copyright__ = "Copyright (c) 2009 Viktor Kerkez"

import io
import os
import sys
import time
import posix
import psutil
import signal
import logging
import tempfile
import threading
import subprocess
from tea.process import base
from tea.decorators import docstring

logger = logging.getLogger(__name__)


def _list_processes():
    for p in psutil.process_iter():
        try:
            try:
                cmdline = p.cmdline()
            except Exception:
                cmdline = [p.exe()]
            yield PosixProcess.immutable(p.pid, cmdline)
        except Exception:
            pass


@docstring(base.doc_kill)
def kill(pid):
    if pid == posix.getpgid(pid):
        os.killpg(pid, signal.SIGKILL)
    else:
        os.kill(pid, signal.SIGKILL)


def _get_cmd(command, arguments):
    """Merge command with arguments."""
    if arguments is None:
        arguments = []
    if command.endswith(".py") or command.endswith(".pyw"):
        return [sys.executable, command] + list(arguments)
    else:
        return [command] + list(arguments)


class PosixProcess(base.Process):
    def __init__(
        self,
        command,
        arguments=None,
        env=None,
        stdout=None,
        stderr=None,
        redirect_output=True,
        working_dir=None,
    ):
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
        self._redirect_output = stdout or stderr or redirect_output
        self._working_dir = working_dir
        self._pid = None
        self._immutable = False

    @classmethod
    def immutable(cls, pid, command):
        p = cls(command[0], command[1:])
        p._pid = pid
        p._immutable = True
        return p

    @property
    def command(self):
        return self._commandline[0]

    @property
    def arguments(self):
        return self._commandline[1:]

    def start(self):
        if self._immutable:
            raise NotImplementedError

        if self._redirect_output:
            if self._stdout:
                self._stdout_writer = io.open(self._stdout, "wb")
                self._stdout_reader = io.open(self._stdout, "rb")
            else:
                self._stdout_writer = tempfile.NamedTemporaryFile()
                self._stdout_reader = io.open(self._stdout_writer.name, "rb")

            if self._stderr:
                self._stderr_writer = io.open(self._stderr, "wb")
                self._stderr_reader = io.open(self._stderr, "rb")
            else:
                self._stderr_writer = tempfile.NamedTemporaryFile()
                self._stderr_reader = io.open(self._stderr_writer.name, "rb")
            try:
                self._process = subprocess.Popen(
                    self._commandline,
                    stdin=subprocess.PIPE,
                    stdout=(
                        self._stdout_writer
                        if self._stdout
                        else self._stdout_writer.file
                    ),
                    stderr=(
                        self._stderr_writer
                        if self._stderr
                        else self._stderr_writer.file
                    ),
                    env=self._create_env(self._env),
                    cwd=self._working_dir,
                )
            except OSError:
                raise base.NotFound(
                    'Executable "{}" not found'.format(self.command)
                )
        else:
            try:
                self._process = subprocess.Popen(
                    self._commandline,
                    stdin=None,
                    stdout=io.open(os.devnull, "wb"),
                    stderr=subprocess.STDOUT,
                    env=self._create_env(self._env),
                    cwd=self._working_dir,
                )
            except OSError:
                raise base.NotFound(
                    'Executable "{}" not found'.format(self.command)
                )
        self._wait_thread = threading.Thread(target=self._process.wait)
        self._wait_thread.setDaemon(True)
        self._wait_thread.start()

    def kill(self):
        try:
            if self._process is not None:
                kill(self.pid)
                self._wait_thread.join()
                self._process = None
                return True
            elif self._immutable:
                kill(self.pid)
                return True
            else:
                return None
        except OSError:
            return False

    def wait(self, timeout=None):
        if self._immutable:
            raise NotImplementedError

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
        if self._immutable:
            raise NotImplementedError

        if self._process is None or self._process.returncode is not None:
            return False
        return True

    @property
    def pid(self):
        return self._pid if self._immutable else self._process.pid

    @property
    def exit_code(self):
        if self._immutable:
            raise NotImplementedError

        if self.is_running:
            return None
        return self._process.returncode

    def write(self, string):
        if self._immutable:
            raise NotImplementedError

        if self._redirect_output:
            if string[-1] != b"\n":
                string += b"\n"
            self._process.stdin.write(string)
            self._process.stdin.flush()

    def read(self):
        if self._immutable:
            raise NotImplementedError

        if self._redirect_output:
            return self._stdout_reader.read()
        return b""

    def eread(self):
        if self._immutable:
            raise NotImplementedError

        if self._redirect_output:
            return self._stderr_reader.read()
        return b""
