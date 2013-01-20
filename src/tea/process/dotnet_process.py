__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '01 January 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import os
import re
import sys
import time
import threading

import clr #@UnresolvedImport
clr.AddReference('System.Management')
from System.Diagnostics import Process as DotNetProcess#@UnresolvedImport
from System.Management import ManagementObjectSearcher #@UnresolvedImport


class Process(object):
    def __init__(self, command, arguments=None, environment=None, redirect_output=True):
        self._process  = DotNetProcess()
        self._process.StartInfo.FileName, self._process.StartInfo.Arguments = self._get_cmd(command, [] if arguments is None else arguments)
        if environment is not None:
            for key, value in environment.items(): 
                self._process.StartInfo.EnvironmentVariables.Add(str(key), str(value))
        self._redirect_output = redirect_output
        self._process.StartInfo.UseShellExecute = False
        self._process.StartInfo.CreateNoWindow = True
        self._process.StartInfo.RedirectStandardInput  = redirect_output
        self._process.StartInfo.RedirectStandardOutput = redirect_output
        self._process.StartInfo.RedirectStandardError  = redirect_output
        self._process.OutputDataReceived += self._stdout_handler
        self._process.ErrorDataReceived  += self._stderr_handler
        
        self._stdout = ''
        self._stdout_lock = threading.Lock()
        self._stderr = ''
        self._stderr_lock = threading.Lock()

    def _get_cmd(self, command, arguments):
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
    
    def _stdout_handler(self, sender, outline):
        data = outline.Data
        if data is None: return
        with self._stdout_lock:
            self._stdout += data
    
    def _stderr_handler(self, sender, outline):
        data = outline.Data
        if data is None: return
        with self._stderr_lock:
            self._stderr += outline.Data

    def start(self):
        self._process.Start()
        if self._redirect_output:
            self._process.BeginOutputReadLine()
            self._process.BeginErrorReadLine()

    def kill(self):
        self._process.Kill()

    def wait(self, timeout=None):
        if timeout is not None:
            return self._process.WaitForExit(timeout)
        else:
            while self.is_running():
                time.sleep(1)
            return True

    def is_running(self):
        return not self._process.HasExited
        
    def _get_pid(self):
        return self._process.Id
   
    def _get_exit_code(self):
        if self._process.HasExited:
            return self._process.ExitCode
        return None

    def write(self, string):
        if self._redirect_output:
            self._process.StandardInput.WriteLine(string)
    
    def read(self):
        if self._redirect_output:
            with self._stdout_lock:
                result = self._stdout
                self._stdout = ''
                return result
        return ''
    
    def eread(self):
        if self._redirect_output:
            with self._stderr_lock:
                result = self._stderr
                self._stderr = ''
                return result
        return ''
    
    pid       = property(_get_pid)
    exit_code = property(_get_exit_code)


    @classmethod
    def GetProcesses(cls, sort_by_name=True, cmdline=False):
        '''Retrieves a list of processes sorted by name.
        
        @type  sort_by_name: boolean
        @param sort_by_name: Sort the list by name or by PID
        @type  cmdline: boolean
        @param cmdline: Add process command line to output
        @rtype:  list[tuple(string, string)]
        @return: List of process PID, process name tuples
        '''
        processes = []
        if cmdline:
            searcher = ManagementObjectSearcher('select ProcessID, Caption, CommandLine from Win32_Process')
            for process in searcher.Get():
                processes.append((int(process['ProcessID']), process['Caption'], process['CommandLine'] or ''))
        else:
            searcher = ManagementObjectSearcher('select ProcessID, Caption from Win32_Process')
            for process in searcher.Get():
                processes.append((int(process['ProcessID']), process['Caption']))
        if sort_by_name:
            return sorted(processes, lambda t1, t2: cmp(t1[1], t2[1]) or cmp(t1[0], t2[0]))
        else:
            return sorted(processes, lambda t1, t2: cmp(t1[0], t2[0]) or cmp(t1[1], t2[1]))

    @classmethod
    def Find(name, arg=None):
        '''Find process by name or by argument in command line if arg param is available'''
        if arg is None:
            for pid, process in Process.GetProcesses():
                if process.lower().find(name.lower()) != -1:
                    return process, pid
        else:
            for pid, process, cmdline in Process.GetProcesses(cmdline=True):
                if process.lower().find(name.lower()) != -1:
                    if cmdline is not None and cmdline.lower().find(arg.lower()) != -1:
                        return process, pid
        return None

    @classmethod
    def Kill(pid=None, process=None):
        '''Kills a process by process PID or
        kills a process started by process module.

        @type pid: int
        @param pid: Process ID of the process to kill 
        @type  process: ShellProcess
        @param process: Process started by process module
        '''
        if process is not None:
            process.kill()
        else:
            process = DotNetProcess.GetProcessById(pid)
            process.Kill()
