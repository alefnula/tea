__author__ = "Viktor Kerkez <alefnula@gmail.com>"
__date__ = "01 August 2013"
__copyright__ = "Copyright (c) 2013 Viktor Kerkez"

import os
import abc
import six


doc_kill = """Kills a process by it's process ID.

Args:
    pid (int): Process ID of the process to kill.
"""


class NotFound(Exception):
    pass


class Process(six.with_metaclass(abc.ABCMeta)):
    r"""Abstract base class for platform specific Process class.

    Simple example of Process class usage can be::

        >>> from tea.process import Process
        >>> p = Process('python', ['-c', 'import time;time.sleep(5);print(3)'])
        >>> p.start()
        >>> p.is_running
        True
        >>> p.wait()
        True
        >>> p.read()
        b'3\\n'
        >>> p.eread()
        b''
    """

    def __str__(self):
        return "Process(pid={0.pid}, command={0.command})".format(self)

    __repr__ = __str__

    @staticmethod
    def _create_env(env):
        full_env = {str(key): str(value) for key, value in os.environ.items()}
        if env is not None:
            full_env.update(
                {str(key): str(value) for key, value in env.items()}
            )
        return full_env

    @abc.abstractmethod
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
        """Create a Process object.

        The only required parameter is the command to execute. It's important
        to note that the constructor only initializes the class, it doesn't
        executes the process. To actually execute the process you have to call
        :met:`start`.

        Args:
            command (str): Path to the executable file.
            arguments (list): list of command line arguments passed to the
                command
            env (dict):: Optional additional environment variables that will be
                added to the subprocess environment or that override currently
                set environment variables.
            stdout (str): Path to the file to which standard output would be
                redirected.
            stderr (str): Path to the file to which standard error would be
                redirected.
            redirect_output (bool): `True` if you want to be able to get the
                standard output and the standard error of the subprocess,
                otherwise it will be redirected to /dev/null. If stdout or
                stderr are provided redirect_output will automatically be set
                to `True`.
            working_dir (str): Set the working directory from which the process
                will be started.
        """

    @classmethod
    @abc.abstractmethod
    def immutable(cls, pid, command):
        """Create an immutable process object used for listing processes."""

    @property
    @abc.abstractmethod
    def command(self):
        """Command."""

    @property
    @abc.abstractmethod
    def arguments(self):
        """Arguments."""

    @abc.abstractmethod
    def start(self):
        """Start the process."""

    @abc.abstractmethod
    def kill(self):
        """Kill the process if it's running."""

    @abc.abstractmethod
    def wait(self, timeout=None):
        """Wait for the process to finish.

        It will wait for the process to finish running. If the timeout is
        provided, the function will wait only ``timeout`` amount of seconds and
        then return to it's caller.

        Args:
            timeout (None or int): ``None`` if you want to wait to wait until
                the process actually finishes, otherwise it will wait just the
                ``timeout`` number of seconds.

        Returns:
            bool: Return value only makes sense if you provided the timeout
                parameter. It will indicate if the process actually finished in
                the amount of time specified, i.e. if the we specify 3 seconds
                and the process actually stopped after 3 seconds it will return
                ``True`` otherwise it will return ``False``.
        """

    @property
    @abc.abstractmethod
    def is_running(self):
        """Indicate if the process is still running.

        Returns:
            bool: ``True`` if the process is still running ``False`` otherwise.
        """

    @property
    @abc.abstractmethod
    def pid(self):
        """PID of the process if it is running.

        Returns:
            int: Process id of the running process.
        """

    @property
    @abc.abstractmethod
    def exit_code(self):
        """Exit code if the process has finished running.

        Returns:
            int or None: Exit code or ``None`` if the process is still running.
        """

    @abc.abstractmethod
    def write(self, string):
        """Write a string to the process standard input.

        Args:
            string (str): String to write to the process standard input.
        """

    @abc.abstractmethod
    def read(self):
        """Read from the process standard output.

        Returns:
            str: The data process has written to the standard output if it has
                written anything. If it hasn't or you already read all the data
                process wrote, it will return an empty string.
        """

    @abc.abstractmethod
    def eread(self):
        """Read from the process standard error.

        Returns:
            str: The data process has written to the standard error if it has
                written anything. If it hasn't or you already read all the data
                process wrote, it will return an empty string.
        """
