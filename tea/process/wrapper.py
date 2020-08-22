__all__ = [
    "execute",
    "execute_and_report",
    "Process",
    "find",
    "get_processes",
    "kill",
]

import os
import logging
from functools import cmp_to_key
from tea.utils import cmp

from tea.process.posix_process import PosixProcess as Process
from tea.process.posix_process import _list_processes, kill


logger = logging.getLogger(__name__)


def get_processes(sort_by_name=True):
    """Retrieve a list of processes sorted by name.

    Args:
        sort_by_name (bool): Sort the list by name or by process ID's.

    Returns:
        list of (int, str) or list of (int, str, str): List of process id,
            process name and optional cmdline tuples.
    """
    if sort_by_name:
        return sorted(
            _list_processes(),
            key=cmp_to_key(
                lambda p1, p2: (cmp(p1.name, p2.name) or cmp(p1.pid, p2.pid))
            ),
        )
    else:
        return sorted(
            _list_processes(),
            key=cmp_to_key(
                lambda p1, p2: (cmp(p1.pid, p2.pid) or cmp(p1.name, p2.name))
            ),
        )


def find(name, arg=None):
    """Find process by name or by argument in command line.

    Args:
        name (str): Process name to search for.
        arg (str): Command line argument for a process to search for.

    Returns:
        tea.process.base.IProcess: Process object if found.
    """
    for p in get_processes():
        if p.name.lower().find(name.lower()) != -1:
            if arg is not None:
                for a in p.cmdline or []:
                    if a.lower().find(arg.lower()) != -1:
                        return p
            else:
                return p
    return None


def execute(command, *args, **kwargs):
    """Execute a command with arguments and wait for output.

    Arguments should not be quoted!

    Keyword Arguments:
        env (dict): Dictionary of additional environment variables.
        wait (bool): Wait for the process to finish.

    Example::

        >>> code = 'import sys;sys.stdout.write('out');sys.exit(0)'
        >>> status, out, err = execute('python', '-c', code)
        >>> print('status: %s, output: %s, error: %s' % (status, out, err))
        status: 0, output: out, error:
        >>> code = 'import sys;sys.stderr.write('out');sys.exit(1)'
        >>> status, out, err = execute('python', '-c', code)
        >>> print('status: %s, output: %s, error: %s' % (status, out, err))
        status: 1, output: , error: err
    """
    wait = kwargs.pop("wait", True)
    process = Process(command, args, env=kwargs.pop("env", None))
    process.start()
    if not wait:
        return process
    process.wait()
    return process.exit_code, process.read(), process.eread()


def execute_and_report(command, *args, **kwargs):
    """Execute a command with arguments and wait for output.

    If execution was successful function will return True,
    if not, it will log the output using standard logging and return False.
    """
    logging.info("Execute: %s %s" % (command, " ".join(args)))
    try:
        status, out, err = execute(command, *args, **kwargs)
        if status == 0:
            logging.info(
                "%s Finished successfully. Exit Code: 0.",
                os.path.basename(command),
            )
            return True
        else:
            try:
                logging.error(
                    "%s failed! Exit Code: %s\nOut: %s\nError: %s",
                    os.path.basename(command),
                    status,
                    out,
                    err,
                )
            except Exception as e:
                # This fails when some non ASCII characters are returned
                # from the application
                logging.error(
                    "%s failed [%s]! Exit Code: %s\nOut: %s\nError: %s",
                    e,
                    os.path.basename(command),
                    status,
                    repr(out),
                    repr(err),
                )
            return False
    except Exception:
        logging.exception(
            "%s failed! Exception thrown!", os.path.basename(command)
        )
        return False
