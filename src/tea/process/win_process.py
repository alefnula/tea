__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '01 January 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import os
import re
import sys
import psutil
import tempfile
import win32api
import win32con
import win32pipe
import win32file
import win32event
import win32process
import win32security

from tea.process import base
from tea.decorators import docstring


@docstring(base.doc_get_processes)
def get_processes(sort_by_name=True, cmdline=False):
    if cmdline:
        processes = [(p.pid, p.name, p.cmdline)
                     for p in psutil.get_process_list()]
    else:
        processes = [(p.pid, p.name) for p in psutil.get_process_list()]
    if sort_by_name:
        return sorted(processes, lambda t1, t2: (cmp(t1[1], t2[1]) or
                                                 cmp(t1[0], t2[0])))
    else:
        return sorted(processes, lambda t1, t2: (cmp(t1[0], t2[0]) or
                                                 cmp(t1[1], t2[1])))


@docstring(base.doc_find)
def find(name, arg=None):
    if arg is None:
        for pid, process in get_processes():
            if process.lower().find(name.lower()) != -1:
                return pid, process
    else:
        for pid, process, cmdline in get_processes(cmdline=True):
            if process.lower().find(name.lower()) != -1:
                if (cmdline is not None and
                        cmdline.lower().find(arg.lower()) != -1):
                    return pid, process
    return None


@docstring(base.doc_kill)
def kill(pid):
    process = WinProcess(
        os.path.join(os.environ['windir'], 'system32', 'taskkill.exe'),
        ['/PID', str(pid), '/F', '/T']
    )
    process.start()
    process.wait()
    return process.exit_code == 0


def create_file(filename, mode='rw'):
    if mode == 'r':
        desired_access = win32con.GENERIC_READ
    elif mode == 'w':
        desired_access = win32con.GENERIC_WRITE
    elif mode in ('rw', 'wr'):
        desired_access = win32con.GENERIC_READ | win32con.GENERIC_WRITE
    else:
        raise ValueError('Invalid access mode')
    share_mode = (win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE |
                  win32con.FILE_SHARE_DELETE)
    attributes = win32security.SECURITY_ATTRIBUTES()
    creation_disposition = win32con.OPEN_ALWAYS
    flags_and_attributes = win32con.FILE_ATTRIBUTE_NORMAL

    handle = win32file.CreateFile(filename, desired_access, share_mode,
                                  attributes, creation_disposition,
                                  flags_and_attributes, 0)
    return handle


def _get_cmd(command, arguments):
    if arguments is None:
        arguments = []
    if command.endswith('.py'):
        arguments = ['%s\\python.exe' % sys.prefix, command] + list(arguments)
    elif command.endswith('.pyw'):
        arguments = ['%s\\pythonw.exe' % sys.prefix, command] + list(arguments)
    else:
        arguments = [command] + list(arguments)
    args = []
    for argument in arguments:
        if re.search(r'\s', argument):
            args.append(r'"%s"' % argument)
        else:
            args.append(argument)
    return ' '.join(args)


class WinProcess(base.Process):
    def __init__(self, command, arguments=None, env=None, redirect_output=True,
                 working_dir=None):
        self._commandline = _get_cmd(command, arguments)
        self._env = env
        self._redirect_output = redirect_output
        self._appName = None
        self._bInheritHandles = 1
        self._processAttributes = win32security.SECURITY_ATTRIBUTES()
        # TODO: Is this needed?
        #self._processAttributes.bInheritHandle = self._bInheritHandles
        self._threadAttributes = win32security.SECURITY_ATTRIBUTES()
        # TODO: Is this needed
        #self._threadAttributes.bInheritHandle = self._bInheritHandles
        self._dwCreationFlags = win32con.CREATE_NO_WINDOW
        # TODO: Which one of these is best?
        #self._dwCreationFlags=win32con.NORMAL_PRIORITY_CLASS
        self._currentDirectory = working_dir
        # This will be created during the start
        self._hProcess = None
        self._hThread = None
        self._dwProcessId = None
        self._dwThreadId = None
        self._exit_code = None

    def _create_pipes(self):
        sa = win32security.SECURITY_ATTRIBUTES()
        sa.bInheritHandle = 1
        self._stdin_read, self._stdin_write = win32pipe.CreatePipe(sa, 0)
        win32api.SetHandleInformation(self._stdin_write,
                                      win32con.HANDLE_FLAG_INHERIT, 0)
        self._stdout = tempfile.TemporaryFile()
        self._stdout_handle = create_file(self._stdout.name)
        self._stderr = tempfile.TemporaryFile()
        self._stderr_handle = create_file(self._stderr.name)

    def start(self):
        # Set up members of the STARTUPINFO structure.
        self._startupinfo = win32process.STARTUPINFO()
        if self._redirect_output:
            # Create pipes
            self._create_pipes()
            self._startupinfo.hStdInput = self._stdin_read
            self._startupinfo.hStdOutput = self._stdout_handle
            self._startupinfo.hStdError = self._stderr_handle
            self._startupinfo.dwFlags |= win32process.STARTF_USESTDHANDLES
        (
            self._hProcess, self._hThread, self._dwProcessId, self._dwThreadId
        ) = win32process.CreateProcess(
            self._appName, self._commandline, self._processAttributes,
            self._threadAttributes, self._bInheritHandles,
            self._dwCreationFlags, self._create_env(self._env),
            self._currentDirectory, self._startupinfo
        )

    def kill(self):
        return kill(self.pid)

    def wait(self, timeout=None):
        if timeout is None:
            while self.is_running:
                win32api.Sleep(1000)
        else:
            result = win32event.WaitForSingleObject(self._hProcess,
                                                    timeout * 1000)
            if result != win32event.WAIT_OBJECT_0:
                return False
        return True

    @property
    def is_running(self):
        if self._hProcess is None or self._exit_code is not None:
            return False
        exit_code = win32process.GetExitCodeProcess(self._hProcess)
        if exit_code != 259:
            self._exit_code = exit_code
            return False
        return True

    @property
    def pid(self):
        return self._dwProcessId

    @property
    def exit_code(self):
        if self.is_running:
            return None
        return self._exit_code

    def write(self, string):
        if self._redirect_output:
            if not string.endswith('\n'):
                string += '\n'
            win32file.WriteFile(self._stdin_write, string)
            win32file.FlushFileBuffers(self._stdin_write)

    def read(self):
        if self._redirect_output:
            return self._stdout.read()
        return ''

    def eread(self):
        if self._redirect_output:
            return self._stderr.read()
        return ''
