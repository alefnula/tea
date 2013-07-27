__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '01 January 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import os
import logging
from tea.system import platform
if platform.is_a(platform.POSIX):
    from .posix_process import Process
elif platform.is_a(platform.DOTNET):
    from .dotnet_process import Process
elif platform.is_a(platform.WINDOWS):
    from .win_process import Process
else:
    raise platform.not_supported('tea.process')


logger = logging.getLogger(__name__)


def execute(command, *args):
    '''Execute a command with arguments and wait for output.
    Arguments should not be quoted!
    
    >>> print 'status: %s, output: %s, error: %s' % execute('python', '-c', 'import sys;sys.stdout.write("out");sys.stderr.write("err");sys.exit(1)')
    status: 1, output: out, error: err
    '''
    process = Process(command, args)
    process.start()
    process.wait()
    return (process.exit_code, process.read(), process.eread())


def execute_in_environment(environment, command, *args):
    '''Execute a command in a specific environment'''
    e = os.environ.copy()
    e.update(environment)
    logging.info('Execute: %s %s' % (command, ' '.join(args)))
    process = Process(command, args, environment=e)
    process.start()
    process.wait()
    return (process.exit_code, process.read(), process.eread())


def execute_and_report(command, *args):
    '''Executes a command with arguments and wait for output.
    If execution was successful function will return True,
    if not, it will log the output using standard logging and return False.
    '''
    logging.info('Execute: %s %s' % (command, ' '.join(args)))
    status = -1
    out    = ''
    err    = ''
    try:
        status, out, err = execute(command, *args)
    except:
        logging.exception('%s failed! Exception thrown!' % os.path.basename(command))
        return False
    if status == 0:
        logging.info('%s Finished successfully. Exit Code: 0.' % os.path.basename(command))
        return True
    else:
        try:
            logging.error('%s failed! Exit Code: %s\nOut: %s\nError: %s' % (os.path.basename(command), status, out, err))
        except:
            # This fails when some non ASCII characters are returned from the application
            logging.error('%s failed! Exit Code: %s\nOut: %s\nError: %s' % (os.path.basename(command), status, repr(out), repr(err)))            
        return False


def execute_nowait(command, *args):
    '''Execute a command with arguments and doesn't wait for output.
    Arguments should not be quoted!
    
    >>> print 'status: %s, output: %s, error: %s' % execute_nowait('python', '-c', 'import sys;sys.stdout.write("out");sys.stderr.write("err");sys.exit(1)')
    status: None, output: out, error: err
    '''
    process = Process(command, args, redirect_output=False)
    process.start()
    return process


def find_process(name):
    '''Find process by name'''
    return Process.Find(name)


def find_script(executable, script):
    '''Find process by name in command lines'''
    return Process.Find(executable, script)


def get_processes(sort_by_name=True):
    '''Retrieves a list of processes sorted by name.
    
    @type  sort_by_name: boolean
    @param sort_by_name: Sort the list by name or by PID
    @rtype:  list[tuple(string, string)]
    @return: List of process PID, process name tuples
    '''
    return Process.GetProcesses(sort_by_name=sort_by_name)


def get_processes_with_cmdline(sort_by_name=True):
    '''Retreaves a list of processes sorted by name.
    
    @type  sort_by_name: boolean
    @param sort_by_name: Sort the list by name or by pid
    @rtype:  list[tuple(string, string, string)]
    @return: List of (process_pid, proces_name, proces_commandline) tuples
    '''
    return Process.GetProcesses(sort_by_name=sort_by_name, cmdline=True)


def kill_process(process):
    '''Kills a process started by subprocess module
    '''
    Process.Kill(process=process)


def kill_pid(pid):
    '''Kills a process by process PID
    '''
    Process.Kill(pid=pid)
