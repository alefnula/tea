import os
import logging
from functools import cmp_to_key
from typing import List, Generator, Tuple, Union, Dict, Optional

import psutil

from tea.utils import cmp
from tea.process.process import Process


logger = logging.getLogger(__name__)


def _list_processes() -> Generator:
    for p in psutil.process_iter():
        try:
            try:
                cmdline = p.cmdline()
            except Exception:
                cmdline = [p.exe()]
            yield Process.immutable(p.pid, cmdline)
        except Exception:
            pass


def get_processes(sort_by_name: bool = True) -> List[Process]:
    """Retrieve a list of processes sorted by name.

    Args:
        sort_by_name: Sort the list by name or by process ID's.

    Returns:
        List[Process]: List of processes.
    """
    if sort_by_name:
        return sorted(
            _list_processes(),
            key=cmp_to_key(
                lambda p1, p2: (
                    cmp(p1.command, p2.command) or cmp(p1.pid, p2.pid)
                )
            ),
        )
    else:
        return sorted(
            _list_processes(),
            key=cmp_to_key(
                lambda p1, p2: (
                    cmp(p1.pid, p2.pid) or cmp(p1.command, p2.command)
                )
            ),
        )


def find(name: str, arg: Optional[str] = None):
    """Find process by name or by argument in command line.

    Args:
        name: Process name to search for.
        arg: Command line argument for a process to search for.

    Returns:
        tea.process.base.IProcess: Process object if found.
    """
    for p in get_processes():
        if p.command.lower().find(name.lower()) != -1:
            if arg is not None:
                for a in p.command_line or []:
                    if a.lower().find(arg.lower()) != -1:
                        return p
            else:
                return p
    return None


def execute(
    command: Union[str, List[str]],
    env: Optional[Dict[str, str]] = None,
    working_dir: Optional[str] = None,
    wait: bool = True,
) -> Union[Tuple[int, str, str], Process]:
    """Execute a command with arguments and wait for output.

    Arguments should not be quoted!

    Keyword Arguments:
        command: Command to execute.
        env: Environment variables.
        working_dir: Set the working dir.
        wait: Wait for the process to finish.

    Returns:
        Tuple[int, str, str]: (exit_code, stdout, stderr) if wait is `True`
            else the process instance.

    Example::

        >>> code = 'import sys; sys.stdout.write('out'); sys.exit(0)'
        >>> status, out, err = execute(['python', '-c', code])
        >>> print('status: %s, output: %s, error: %s' % (status, out, err))
        status: 0, output: out, error:
        >>> code = 'import sys; sys.stderr.write('out'); sys.exit(1)'
        >>> status, out, err = execute(['python', '-c', code])
        >>> print('status: %s, output: %s, error: %s' % (status, out, err))
        status: 1, output: , error: err
    """
    process = Process(command=command, env=env, working_dir=working_dir)
    process.start()
    if not wait:
        return process
    process.wait()
    return process.exit_code, process.read(), process.eread()


def execute_no_demux(
    command: Union[str, List[str]],
    env: Optional[Dict[str, str]] = None,
    working_dir: Optional[str] = None,
    wait: bool = True,
) -> Union[Tuple[int, str], Process]:
    """Execute a command and return the exit code and output.

    Args:
        command: Command to execute.
        env: Environment variables.
        working_dir: Set the working dir.
        wait: Wait for the process to finish.

    Returns:
        Tuple[int, str, str]: (exit_code, stdout, stderr) if wait is `True`
            else the process instance.
    """
    process = Process(
        command=command, env=env, working_dir=working_dir, demux=False
    )
    process.start()
    if not wait:
        return process
    process.wait()
    return process.exit_code, process.read()


def execute_and_report(command, *args, **kwargs):
    """Execute a command with arguments and wait for output.

    If execution was successful function will return True,
    if not, it will log the output using standard logging and return False.
    """
    logging.info("Execute: %s" % command)
    try:
        status, out, err = execute(command, *args, **kwargs)
        if status == 0:
            logging.info(
                "%s Finished successfully. Exit Code: 0.",
                os.path.basename(command[0]),
            )
            return True
        else:
            try:
                logging.error(
                    "%s failed! Exit Code: %s\nOut: %s\nError: %s",
                    os.path.basename(command[0]),
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
                    os.path.basename(command[0]),
                    status,
                    repr(out),
                    repr(err),
                )
            return False
    except Exception:
        logging.exception(
            "%s failed! Exception thrown!", os.path.basename(command[0])
        )
        return False
