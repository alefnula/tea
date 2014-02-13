__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '01 January 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import os
import re
import sys
import time
import threading
from tea.process import base
from tea.decorators import docstring

import clr  # @UnresolvedImport
clr.AddReference('System.Management')
from System.Diagnostics import Process as CSharpProcess
from System.Management import ManagementObjectSearcher


@docstring(base.doc_get_processes)
def get_processes(sort_by_name=True, cmdline=False):
    processes = []
    if cmdline:
        searcher = ManagementObjectSearcher(
            'SELECT ProcessID, Caption, CommandLine FROM Win32_Process'
        )
        for process in searcher.Get():
            processes.append((int(process['ProcessID']), process['Caption'],
                              process['CommandLine'] or ''))
    else:
        searcher = ManagementObjectSearcher(
            'SELECT ProcessID, Caption FROM Win32_Process'
        )
        for process in searcher.Get():
            processes.append((int(process['ProcessID']), process['Caption']))
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
    process = CSharpProcess.GetProcessById(pid)
    process.Kill()
    while not process.HasExited:
        time.sleep(0.1)


def _get_cmd(command, arguments):
    if arguments is None:
        arguments = []
    if command.endswith('.py'):
        arguments = [command] + list(arguments)
        command = os.path.join(sys.prefix, 'ipy.exe')
    elif command.endswith('.pyw'):
        arguments = [command] + list(arguments)
        command = os.path.join(sys.prefix, 'ipyw.exe')
    args = []
    for argument in arguments:
        if re.search(r'\s', argument):
            args.append(r'"%s"' % argument)
        else:
            args.append(argument)
    arguments = ' '.join(args)
    return command, arguments


class DotnetProcess(base.Process):
    def __init__(self, command, arguments=None, env=None, redirect_output=True,
                 working_dir=None):
        self._process = CSharpProcess()
        start_info = self._process.StartInfo
        start_info.FileName, start_info.Arguments = _get_cmd(command,
                                                             arguments)
        start_info.CreateNoWindow = True
        start_info.UseShellExecute = not redirect_output
        start_info.RedirectStandardInput = redirect_output
        start_info.RedirectStandardOutput = redirect_output
        start_info.RedirectStandardError = redirect_output
        if working_dir is not None:
            start_info.WorkingDirectory = working_dir
        self._env = env
        self._redirect_output = redirect_output
        self._process.OutputDataReceived += self._stdout_handler
        self._process.ErrorDataReceived += self._stderr_handler

        self._started = False
        self._stdout = b''
        self._stdout_lock = threading.Lock()
        self._stderr = b''
        self._stderr_lock = threading.Lock()

    def _stdout_handler(self, sender, outline):
        data = outline.Data
        if data is None:
            return
        with self._stdout_lock:
            self._stdout += data

    def _stderr_handler(self, sender, outline):
        data = outline.Data
        if data is None:
            return
        with self._stderr_lock:
            self._stderr += outline.Data

    def start(self):
        # Setup environment variables
        process_env = self._process.StartInfo.EnvironmentVariables
        for key, value in self._create_env(self._env).items():
            process_env[unicode(key)] = unicode(value)
        self._process.Start()
        if self._redirect_output:
            self._process.BeginOutputReadLine()
            self._process.BeginErrorReadLine()
        self._started = True

    def kill(self):
        if self._started:
            self._process.Kill()
        self.wait()

    def wait(self, timeout=None):
        if self._started:
            if timeout is not None:
                return self._process.WaitForExit(timeout)
            else:
                while self.is_running:
                    time.sleep(1)
                return True
        return False

    @property
    def is_running(self):
        return not self._process.HasExited if self._started else False

    @property
    def pid(self):
        return self._process.Id if self._started else 0

    @property
    def exit_code(self):
        if self._started and self._process.HasExited:
            return self._process.ExitCode
        return None

    def write(self, string):
        if self._redirect_output:
            self._process.StandardInput.WriteLine(string)

    def read(self):
        if self._redirect_output:
            with self._stdout_lock:
                result = self._stdout
                self._stdout = b''
                return result
        return b''

    def eread(self):
        if self._redirect_output:
            with self._stderr_lock:
                result = self._stderr
                self._stderr = b''
                return result
        return b''
