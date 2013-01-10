__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '01 January 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import os
import re
import sys
import tempfile

import wmi
import pythoncom

import win32api
import win32con
import win32pipe
import win32file
import win32event
import win32process
import win32security


def create_file(filename, mode='rw'):
    if mode == 'r':
        desiredAccess = win32con.GENERIC_READ
    elif mode == 'w':
        desiredAccess = win32con.GENERIC_WRITE
    elif mode in ('rw', 'wr'):
        desiredAccess = win32con.GENERIC_READ | win32con.GENERIC_WRITE
    else:
        raise ValueError('Invalid access mode')
    shareMode = win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE
    attributes =  win32security.SECURITY_ATTRIBUTES()
    creationDisposition = win32con.OPEN_ALWAYS
    flagsAndAttributes = win32con.FILE_ATTRIBUTE_NORMAL
    
    handle = win32file.CreateFile(filename, desiredAccess, shareMode, attributes, creationDisposition,
                                  flagsAndAttributes, 0)
    return handle



class Process(object):
    def __init__(self, command, arguments=None, environment=None, redirect_output=True):
        # Parse and generate the command line
        self._commandline       = self._get_cmd(command, [] if arguments is None else arguments)
        self._environment       = dict((str(key), str(value)) for key, value in environment.items()) if environment else None 
        self._redirect_output   = redirect_output
        self._appName           = None
        self._bInheritHandles   = 1
        self._processAttributes = win32security.SECURITY_ATTRIBUTES()
        # FIXME: Vidi jel treba ovo: self._processAttributes.bInheritHandle = self._bInheritHandles
        self._threadAttributes  = win32security.SECURITY_ATTRIBUTES()
        # FIXME: Vidi jel treba ovo: self._threadAttributes.bInheritHandle = self._bInheritHandles
        self._dwCreationFlags   = win32con.CREATE_NO_WINDOW
        # FIXME: Vidi koji od ovih je najbolji: self._dwCreationFlags=win32con.NORMAL_PRIORITY_CLASS
        self._currentDirectory  = None # string or None
        # This will be created during the start
        self._hProcess    = None
        self._hThread     = None
        self._dwProcessId = None
        self._dwThreadId  = None
        self._exit_code   = None

    def _get_cmd(self, command, arguments):
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

    def _create_pipes(self):
        # Create pipes for process STDIN, STDOUT and STDERR
        # Set the bInheritHandle flag so pipe handles are inherited. 
        sa = win32security.SECURITY_ATTRIBUTES()
        sa.bInheritHandle = 1
        # FIXME: Vidi sta je sa ovim atributom: sa.lpSecurityDescriptor = None
        # Create a pipe for the child process's STDIN.
        # Ensure that the write handle to the child process's pipe for STDIN is not inherited.
        self._stdin_read, self._stdin_write = win32pipe.CreatePipe(sa, 0)
        win32api.SetHandleInformation(self._stdin_write, win32con.HANDLE_FLAG_INHERIT, 0)
        # Create a pipe for the child process's STDOUT.
        # Ensure that the read handle to the child process's pipe for STDOUT is not inherited. 
        #self._stdout_read, self._stdout_write = win32pipe.CreatePipe(sa, 0)
        #win32api.SetHandleInformation(self._stdout_read, win32con.HANDLE_FLAG_INHERIT, 0)
        # Create a pipe for the child process's STDERR.
        # Ensure that the read handle to the child process's pipe for STDERR is not inherited.
        #self._stderr_read, self._stderr_write = win32pipe.CreatePipe(sa, 0)
        #win32api.SetHandleInformation(self._stderr_read, win32con.HANDLE_FLAG_INHERIT, 0)
        #self._stdin = tempfile.TemporaryFile()
        #self._stdin_handle = create_file(self._stdin.name)
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
            self._startupinfo.hStdInput  = self._stdin_read
            #self._startupinfo.hStdOutput = self._stdout_write
            #self._startupinfo.hStdError  = self._stderr_write
            #self._startupinfo.hStdInput  = self._stdin_handle
            self._startupinfo.hStdOutput = self._stdout_handle
            self._startupinfo.hStdError  = self._stderr_handle
            self._startupinfo.dwFlags |= win32process.STARTF_USESTDHANDLES            
        self._hProcess, self._hThread, self._dwProcessId, self._dwThreadId = \
            win32process.CreateProcess(self._appName, self._commandline, self._processAttributes,
                                       self._threadAttributes, self._bInheritHandles,
                                       self._dwCreationFlags, self._environment,
                                       self._currentDirectory, self._startupinfo)

    def kill(self):
        return Process.Kill(self.pid)

    def wait(self, timeout=None):
        if timeout is None:
            while self.is_running():
                win32api.Sleep(1000)
        else:
            if win32event.WaitForSingleObject(self._hProcess, timeout*1000) != win32event.WAIT_OBJECT_0:
                return False
        return True

    def is_running(self):
        if self._hProcess is None or self._exit_code is not None:
            return False
        exit_code = win32process.GetExitCodeProcess(self._hProcess)
        if exit_code != 259:
            self._exit_code = exit_code
            return False
        return True

    def _get_pid(self):
        return self._dwProcessId
   
    def _get_exit_code(self):
        if self.is_running():
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

#    def _get_stdout(self):
#        return self._stdout.read()
#        #if self._stdout is None:
#        #    if self.is_running():
#        #        return ''
#        #    else:
#        #        win32file.CloseHandle(self._stdout_write)
#        #        size = win32file.GetFileSize(self._stdout_read)
#        #        if size > 0:
#        #            junk, self._stdout = win32file.ReadFile(self._stdout_read, size)
#        #        else:
#        #            self._stdout = ''
#        #return self._stdout


#    def _get_stderr(self):
#        return self._stderr.read()
#        #if self._stderr is None:
#        #    if self.is_running():
#        #        return ''
#        #    else:
#        #        win32file.CloseHandle(self._stderr_write)
#        #        size = win32file.GetFileSize(self._stderr_read)
#        #        if size > 0:
#        #            junk, self._stderr = win32file.ReadFile(self._stderr_read, size)
#        #        else:
#        #            self._stderr = ''
#        #return self._stderr
    
    pid       = property(_get_pid)
    exit_code = property(_get_exit_code)
    #stdin     = property(_get_stdin)
    #stdout    = property(_get_stdout)
    #stderr    = property(_get_stderr)



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
        
        '''if 'win' in sys.platform:
            win32pdh.EnumObjects(None, None, win32pdh.PERF_DETAIL_WIZARD)
            junk, instances = win32pdh.EnumObjectItems(None,None,'Process', win32pdh.PERF_DETAIL_WIZARD)
        
            proc_dict = {}
            for instance in instances:
                if proc_dict.has_key(instance):
                    proc_dict[instance] = proc_dict[instance] + 1
                else:
                    proc_dict[instance] = 1
        
            
            for instance, max_instances in proc_dict.items():
                for inum in xrange(max_instances):
                    hq = win32pdh.OpenQuery() # initializes the query handle 
                    try:
                        path = win32pdh.MakeCounterPath( (None, 'Process', instance, None, inum, 'ID Process') )
                        counter_handle = win32pdh.AddCounter(hq, path) #convert counter path to counter handle
                        try:
                            win32pdh.CollectQueryData(hq) #collects data for the counter 
                            type, val = win32pdh.GetFormattedCounterValue(counter_handle, win32pdh.PDH_FMT_LONG)
                            processes.append((instance, val))
                        except win32pdh.error, e:
                            LOG_EXCEPTION('Error retreaving process list')
                        win32pdh.RemoveCounter(counter_handle)
                    except win32pdh.error, e:
                        LOG_EXCEPTION('Error retreaving process list')
                    win32pdh.CloseQuery(hq)
        '''
        processes = []
        pythoncom.CoInitialize() #@UndefinedVariable
        try:
            c = wmi.WMI(find_classes=False)
            if cmdline:
                for i in c.Win32_Process(['ProcessID', 'Caption', 'CommandLine']):
                    processes.append((i.ProcessID, i.Caption, i.CommandLine))
            else:
                for i in c.Win32_Process(['ProcessID', 'Caption']):
                    processes.append((i.ProcessID, i.Caption))
        finally:
            pythoncom.CoUninitialize() #@UndefinedVariable
        if sort_by_name:
            return sorted(processes, lambda t1, t2: cmp(t1[1], t2[1]) or cmp(t1[0], t2[0]))
        else:
            return sorted(processes, lambda t1, t2: cmp(t1[0], t2[0]) or cmp(t1[1], t2[1]))

    @classmethod
    def Find(name, arg=None):
        '''Find process by name or by argument in command line if arg param is available'''
        if arg is None:
            for id, process in Process.GetProcesses():
                if process.lower().find(name.lower()) != -1:
                    return process, id
        else:
            for id, process, cmdline in Process.GetProcesses(cmdline=True):
                if process.lower().find(name.lower()) != -1:
                    if cmdline is not None and cmdline.lower().find(arg.lower()) != -1:
                        return process, id        
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
            pid = process.pid
        # TODO: Proveriti return value i ako je False - GetLastError
        #win32process.TerminateProcess(int(process._handle), -1)
        # TODO:
        #PROCESS_TERMINATE = 1
        #handle = win32api.OpenProcess(PROCESS_TERMINATE, False, pid)
        #win32api.TerminateProcess(handle, -1)
        #win32api.CloseHandle(handle)
        process = Process(os.path.join(os.environ['windir'], 'system32', 'taskkill.exe'), ['/PID', str(pid), '/F', '/T'])
        process.start()
        process.wait()
        #ctypes.windll.kernel32.TerminateProcess(int(process._handle), -1)
        return process.exit_code == 0
