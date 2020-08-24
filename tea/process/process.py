import io
import os
import time
import posix
import signal
import logging
import tempfile
import threading
import subprocess
from typing import Optional, Dict, Union, List

from tea.errors import TeaError


logger = logging.getLogger(__name__)


class ExecutableNotFound(TeaError):
    def __init__(self, command):
        self.command = command
        super().__init__(message=f"Executable not found: {command}")


def _create_env(env):
    full_env = {str(key): str(value) for key, value in os.environ.items()}
    if env is not None:
        full_env.update({str(key): str(value) for key, value in env.items()})
    return full_env


def kill(pid):
    """Kills a process by it's process ID.

    Args:
        pid (int): Process ID of the process to kill.
    """
    if pid == posix.getpgid(pid):
        os.killpg(pid, signal.SIGKILL)
    else:
        os.kill(pid, signal.SIGKILL)


class Process:
    r"""Process class.

    Simple example of Process class usage can be::

        >>> from tea.process import Process
        >>> p = Process('python', ['-c', 'import time;time.sleep(5);print(3)'])
        >>> p.start()
        >>> p.is_running
        True
        >>> p.wait()
        True
        >>> p.read()
        '3\\n'
        >>> p.eread()
        ''
    """

    def __init__(
        self,
        command: Union[str, List[str]],
        env: Optional[Dict[str, str]] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        demux: bool = True,
        redirect_output: bool = True,
        working_dir: Optional[str] = None,
        encoding: str = "utf-8",
    ):
        """Create a Process object.

        The only required parameter is the command to execute. It's important
        to note that the constructor only initializes the class, it doesn't
        executes the process. To actually execute the process you have to call
        the `start` method.

        Args:
            command: Path to the executable file or a list with the full
                command and it's arguments.
            env: Optional additional environment variables that will be added
                to the subprocess environment or that override currently set
                environment variables.
            stdout: Path to the file to which standard output would be
                redirected.
            stderr: Path to the file to which standard error would be
                redirected.
            demux: Demux stdout and stderr. Default: `True`. If demux is set to
                `False` `eread` will always return an empty string and all
                stderr will be redirected to stdout.
            redirect_output: `True` if you want to be able to get the standard
                output and the standard error of the subprocess, otherwise it
                will be redirected to /dev/null. If stdout or stderr are
                provided redirect_output will automatically be set to `True`.
            working_dir: Set the working directory from which the process will
                be started.
            encoding: Encoding to use to decode the standard output and
                standard error.
        """
        self._commandline = [command] if isinstance(command, str) else command
        self._env = env
        self._process = None
        self._wait_thread = None
        self._stdout = os.path.abspath(stdout) if stdout else None
        self._stdout_reader = None
        self._stdout_writer = None
        self._stderr = os.path.abspath(stderr) if stderr else None
        self._stderr_reader = None
        self._stderr_writer = None
        self._demux = demux
        self._redirect_output = stdout or stderr or redirect_output
        self._working_dir = working_dir
        self._encoding = encoding
        self._pid = None
        self._immutable = False

    def __process_wait(self):
        self._process.wait()
        if self._stdout is not None:
            if (
                self._stdout_writer is not None
                and not self._stdout_writer.closed
            ):
                self._stdout_writer.close()
        if self._demux and self._stderr is not None:
            if (
                self._stderr_writer is not None
                and not self._stderr_writer.closed
            ):
                self._stderr_writer.close()

    @classmethod
    def immutable(cls, pid, command):
        """Create an immutable process object used for listing processes."""
        p = cls(command[0], command[1:])
        p._pid = pid
        p._immutable = True
        return p

    @property
    def command(self):
        """Command."""
        return self._commandline[0]

    @property
    def arguments(self):
        """Arguments."""
        return self._commandline[1:]

    @property
    def command_line(self):
        """Full command line."""
        return self._commandline

    def start(self):
        """Start the process."""
        if self._immutable:
            raise NotImplementedError

        if self._redirect_output:
            if self._stdout:
                self._stdout_writer = io.open(self._stdout, "wb")
                self._stdout_reader = io.open(self._stdout, "rb")
            else:
                self._stdout_writer = tempfile.NamedTemporaryFile()
                self._stdout_reader = io.open(self._stdout_writer.name, "rb")

            if self._demux:
                if self._stderr:
                    self._stderr_writer = io.open(self._stderr, "wb")
                    self._stderr_reader = io.open(self._stderr, "rb")
                else:
                    self._stderr_writer = tempfile.NamedTemporaryFile()
                    self._stderr_reader = io.open(
                        self._stderr_writer.name, "rb"
                    )
            else:
                self._stderr_writer = self._stdout_writer
                self._stderr_reader = self._stdout_reader

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
                    env=_create_env(self._env),
                    cwd=self._working_dir,
                )
            except OSError:
                raise ExecutableNotFound(command=self.command)
        else:
            try:
                self._process = subprocess.Popen(
                    self._commandline,
                    stdin=None,
                    stdout=io.open(os.devnull, "wb"),
                    stderr=subprocess.STDOUT,
                    env=_create_env(self._env),
                    cwd=self._working_dir,
                )
            except OSError:
                raise ExecutableNotFound(command=self.command)
        self._wait_thread = threading.Thread(
            target=self.__process_wait, daemon=True
        )
        self._wait_thread.start()

    def kill(self):
        """Kill the process if it's running."""
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

    def wait(self, timeout: Optional[int] = None):
        """Wait for the process to finish.

        It will wait for the process to finish running. If the timeout is
        provided, the function will wait only `timeout` amount of seconds and
        then return to it's caller.

        Args:
            timeout: `None` if you want to wait to wait until the process
                actually finishes, otherwise it will wait just the `timeout`
                number of seconds.

        Returns:
            bool: Return value only makes sense if you provided the timeout
                parameter. It will indicate if the process actually finished in
                the amount of time specified, i.e. if the we specify 3 seconds
                and the process actually stopped after 3 seconds it will return
                `True` otherwise it will return `False`.
        """
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
        """Indicate if the process is still running.

        Returns:
            bool: `True` if the process is still running `False` otherwise.
        """
        if self._immutable:
            raise NotImplementedError

        if self._process is None or self._process.returncode is not None:
            return False
        return True

    @property
    def pid(self):
        """PID of the process if it is running.

        Returns:
            int: Process id of the running process.
        """
        return self._pid if self._immutable else self._process.pid

    @property
    def exit_code(self) -> Optional[int]:
        """Exit code if the process has finished running.

        Returns:
            Optional[int]: Exit code or `None` if the process is still running.
        """
        if self._immutable:
            raise NotImplementedError

        if self.is_running:
            return None
        return self._process.returncode

    def write(self, string: str):
        """Write a string to the process standard input.

        Args:
            string: String to write to the process standard input.
        """
        if self._immutable:
            raise NotImplementedError

        if self._redirect_output:
            if string[-1] != "\n":
                string += "\n"
            self._process.stdin.write(string.encode(self._encoding))
            self._process.stdin.flush()

    def read(self) -> str:
        """Read from the process standard output.

        Returns:
            str: The data process has written to the standard output if it has
                written anything. If it hasn't or you already read all the data
                process wrote, it will return an empty string.
        """
        if self._immutable:
            raise NotImplementedError

        if self._redirect_output:
            return self._stdout_reader.read().decode(self._encoding)
        return ""

    def eread(self) -> str:
        """Read from the process standard error.

        Returns:
            str: The data process has written to the standard error if it has
                written anything. If it hasn't or you already read all the data
                process wrote, it will return an empty string.
        """
        if self._immutable:
            raise NotImplementedError

        if self._redirect_output and self._demux:
            return self._stderr_reader.read().decode("utf-8")
        return ""

    def __del__(self):
        if self._stdout is not None:
            if (
                self._stdout_reader is not None
                and not self._stdout_reader.closed
            ):
                self._stdout_reader.close()
        if self._demux and self._stderr is not None:
            if (
                self._stderr_reader is not None
                and not self._stderr_reader.closed
            ):
                self._stderr_reader.close()

    def __str__(self):
        return f"Process(pid={self.pid}, command={self.command})"

    __repr__ = __str__
