__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '27 November 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import win32api  # @UnresolvedImport
import win32con  # @UnresolvedImport
import win32file  # @UnresolvedImport
import win32security  # @UnresolvedImport


class WindowsFile(object):
    def __init__(self, filename, mode='r', encoding=None):
        if mode in ('r', 'r+'):
            creationDisposition = win32file.OPEN_EXISTING
            desiredAccess = win32con.GENERIC_READ
        elif mode == 'w':
            creationDisposition = win32con.CREATE_ALWAYS
            desiredAccess = win32con.GENERIC_WRITE
        elif mode in ('rw', 'wr', 'r+', 'w+', 'a+'):
            creationDisposition = win32con.OPEN_ALWAYS
            desiredAccess = win32con.GENERIC_READ | win32con.GENERIC_WRITE
        elif mode == 'a':
            creationDisposition = win32con.OPEN_ALWAYS
            desiredAccess = win32con.GENERIC_WRITE
        else:
            raise ValueError('Invalid access mode')
        self.filename = filename
        #shareMode = (win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE |
        #             win32con.FILE_SHARE_DELETE)
        shareMode = win32con.shareMode = (win32con.FILE_SHARE_READ |
                                          win32con.FILE_SHARE_WRITE)
        attributes = win32security.SECURITY_ATTRIBUTES()
        #dwFlagsAndAttributes = win32con.FILE_ATTRIBUTE_NORMAL
        dwFlagsAndAttributes = win32con.FILE_FLAG_WRITE_THROUGH

        self.encoding = encoding or 'utf-8'
        self.handle = win32file.CreateFile(filename, desiredAccess, shareMode,
                                           attributes, creationDisposition,
                                           dwFlagsAndAttributes, 0)
        win32api.SetHandleInformation(self.handle,
                                      win32con.HANDLE_FLAG_INHERIT, 0)
        if mode in ('a', 'a+'):
            self.seek(0, 2)
        self.file_size = win32file.GetFileSize(self.handle)
        self.is_closed = False

    def __iter__(self):
        return self

    def __next__(self):
        line = self.readline()
        if line != '':
            return line
        raise StopIteration

    def __enter__(self):
        return

    def __exit__(self, *exc_info):
        self.close()

    def write(self, s):
        status, written = win32file.WriteFile(self.handle,
                                              s.replace('\n', '\r\n')
                                               .encode(self.encoding), None)
        #win32file.FlushFileBuffers(self.handle)
        return status

    def writelines(self, string_list):
        for string in string_list:
            self.write(string + '\n')

    def close(self):
        win32file.CloseHandle(self.handle)
        self.is_closed = True

    def get_closed(self):
        if self.is_closed:
            return True
        return False
    closed = property(get_closed)

    def seek(self, offset, moveMethod=0):
        if moveMethod == 0:
            position = win32file.FILE_BEGIN
        elif moveMethod == 1:
            position = win32file.FILE_CURRENT
        elif moveMethod == 2:
            position = win32file.FILE_END
        else:
            raise ValueError('Invalid move method')
        win32file.SetFilePointer(self.handle, offset, position)

    def tell(self):
        return win32file.SetFilePointer(self.handle, 0, win32file.FILE_CURRENT)

    def read(self, bytesToRead=None):
        if bytesToRead is None:
            bytesToRead = self.file_size
        hr, data = win32file.ReadFile(self.handle, bytesToRead, None)
        return data.replace('\r', '')

    def readline(self, bytesToRead=None):
        pos = self.tell()
        if bytesToRead is not None:
            data = self.read(bytesToRead)
            index = data.find('\n')
            if index == -1:
                return data
            else:
                self.seek(pos + index + 2)
                return data.split('\n')[0] + '\n'
        else:
            all_data = ''
            bytesToRead = 100
            data = self.read(bytesToRead)
            while not len(data) == 0:
                all_data += data
                index = data.find('\n')
                if index == -1:
                    pos += bytesToRead
                if index != -1:
                    self.seek(pos + index + 2)
                    return all_data.split('\n')[0] + '\n'
                data = self.read(bytesToRead)
            return all_data

    def readlines(self):
        lines = []
        data = self.readline()
        while data != '':
            lines.append(data)
            data = self.readline()
        return lines

    def flush(self):
        if not self.is_closed:
            win32file.FlushFileBuffers(self.handle)


win_file = WindowsFile
win_open = WindowsFile
