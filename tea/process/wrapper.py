__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '01 January 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

__all__ = ['execute', 'execute_and_report', 'Process', 'find', 'get_processes',
           'kill']

import os
import logging

from tea.system import platform
if platform.is_a(platform.POSIX):
    from .posix_process import PosixProcess as Process
    from .posix_process import find, get_processes, kill
elif platform.is_a(platform.DOTNET):
    from .dotnet_process import DotnetProcess as Process
    from .dotnet_process import find, get_processes, kill
elif platform.is_a(platform.WINDOWS):
    from .win_process import WinProcess as Process
    from .win_process import find, get_processes, kill
else:
    raise platform.not_supported('tea.process')


logger = logging.getLogger(__name__)


def execute(command, *args, **kwargs):
    """Execute a command with arguments and wait for output.
    Arguments should not be quoted!

    Keyword arguments:

    :param dict env: Dictionary of additional environment variables.
    :param bool wait: Wait for the process to finish.

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
    wait = kwargs.pop('wait', True)
    process = Process(command, args, env=kwargs.pop('env', None))
    process.start()
    if not wait:
        return process
    process.wait()
    return process.exit_code, process.read(), process.eread()


def execute_and_report(command, *args, **kwargs):
    """Executes a command with arguments and wait for output.
    If execution was successful function will return True,
    if not, it will log the output using standard logging and return False.
    """
    logging.info('Execute: %s %s' % (command, ' '.join(args)))
    try:
        status, out, err = execute(command, *args, **kwargs)
        if status == 0:
            logging.info('%s Finished successfully. Exit Code: 0.',
                         os.path.basename(command))
            return True
        else:
            try:
                logging.error('%s failed! Exit Code: %s\nOut: %s\nError: %s',
                              os.path.basename(command), status, out, err)
            except:
                # This fails when some non ASCII characters are returned
                # from the application
                logging.error('%s failed! Exit Code: %s\nOut: %s\nError: %s',
                              os.path.basename(command), status, repr(out),
                              repr(err))
            return False
    except:
        logging.exception('%s failed! Exception thrown!',
                          os.path.basename(command))
        return False
