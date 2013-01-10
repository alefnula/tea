__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '27 November 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

__doc__ = '''
This module mimics the behavior of the builtin module B{shutil} from the
standard python library, adding logging to all operations.

Also, it adds a few useful additional functions to the module.
'''

import os
import shutil
import fnmatch
from tea.logger import *


def search(path, matcher='*', dirs=False, files=True):
    '''Recursive search function.
    
    @param path: path to search recursively
    @param matcher: string pattern to search for or function that returns True/False for a file argument
    @param dirs: if True returns also directories that match the pattern
    '''
    if callable(matcher):
        fnmatcher = lambda items: filter(matcher, items)
    else:
        fnmatcher = lambda items: fnmatch.filter(items, matcher)
    for root, directories, filenames in os.walk(os.path.abspath(path)):
        items = []
        if dirs:  items.extend(directories)
        if files: items.extend(filenames)
        for item in fnmatcher(items):
            yield os.path.join(root, item)


def chdir(directory):
    '''Change the current working directory'''
    directory = os.path.abspath(directory)
    LOG_INFO('chdir -> %s' % directory)
    try:
        if not os.path.isdir(directory):
            LOG_ERROR('chdir -> %s failed! Directory does not exist!' % directory)
            return False
        os.chdir(directory)
        return True
    except Exception, e:
        LOG_ERROR('chdir -> %s failed! %s' % (directory, e))
        return False


class goto(object):
    '''Context object for changing directory.
    
    Usage:
    >>> with goto(directory) as ok:
    ...     if not ok:
    ...         print 'Error'
    ...     else:
    ...         print 'All OK'
    '''
    def __init__(self, directory, create=False):
        self.current   = os.getcwd()
        self.directory = os.path.abspath(directory)
        self.create    = create

    def __enter__(self):
        if not os.path.isdir(self.directory):
            if self.create:
                LOG_INFO('goto(%s) Directory does not exist, creating.' % self.directory)
                if not mkdir(self.directory):
                    LOG_ERROR('goto(%s) Could not create directory.' % self.directory)
                    return False
            else:
                LOG_ERROR('goto(%s) failed! Directory does not exist!' % self.directory)
                return False
        LOG_INFO('goto -> %s' % self.directory)
        os.chdir(self.directory)
        return True

    def __exit__(self, exc_type, exc_value, traceback):
        LOG_INFO('goto <- %s' % self.directory)
        os.chdir(self.current)


def mkdir(path, mode=0777, delete=False):
    '''mkdir(path [, mode=0777])
    
    Create a leaf directory and all intermediate ones.
    Works like mkdir, except that any intermediate path segment (not
    just the rightmost) will be created if it does not exist.  This is
    recursive.
    
    @param path:   directory to create
    @param mode:   directory mode
    @param delete: delete directory/file if exists
    '''
    LOG_INFO('mkdir: %s' % path)
    if os.path.isdir(path):
        if not delete: return True
        if not remove(path): return False
    try:
        os.makedirs(path, mode)
        return True
    except:
        LOG_EXCEPTION('Failed to mkdir: %s' % path)
        return False


def copyfile(source, destination):
    '''Copy data and mode bits ("cp source destination").

    The destination may be a directory.
    
    @type  source: string
    @param source: Source file (file to copy).
    @type  destination: string
    @param destination: Destination file or directory (where to copy).
    @rtype:  boolean
    @return: True if the operation is successful, False otherwise. 
    '''
    LOG_INFO('copyfile: %s -> %s' % (source, destination))
    try:
        shutil.copy(source, destination)
        return True
    except Exception, e:
        LOG_ERROR('copyfile: %s -> %s failed! Error: %s' % (source, destination, e))
        return False


def copyfile2(source, destination):
    '''Copy data and all stat info ("cp -p source destination").

    The destination may be a directory.
    
    @type  source: string
    @param source: Source file (file to copy).
    @type  destination: string
    @param destination: Destination file or directory (where to copy).
    @rtype:  boolean
    @return: True if the operation is successful, False otherwise. 
    '''
    LOG_INFO('copyfile2: %s -> %s' % (source, destination))
    try:
        shutil.copy2(source, destination)
        return True
    except Exception, e:
        LOG_ERROR('copyfile2: %s -> %s failed! Error: %s' % (source, destination, e))
        return False
    

def copytree(source, destination, symlinks=False):
    '''Recursively copy a directory tree using copy2().
    
    The destination directory must not already exist.

    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied.
    
    @type  source: string
    @param source: Source directory (directory to copy).
    @type  destination: string
    @param destination: Destination directory (where to copy).
    @type  symlinks: boolean
    @param symlinks: Follow symbolic links.
    @rtype:  boolean
    @return: True if the operation is successful, False otherwise.
    '''
    LOG_INFO('copytree: %s -> %s' % (source, destination))
    try:
        shutil.copytree(source, destination, symlinks)
        return True
    except Exception, e:
        LOG_EXCEPTION('copytree: %s -> %s failed! Error: %s' % (source, destination, e))
        return False


def copy(source, destination):
    '''Copy file or directory'''
    if os.path.isdir(source):
        copytree(source, destination)
    else:
        copyfile2(source, destination)
    

def move(source, destination):
    '''Recursively move a file or directory to another location.
    
    If the destination is on our current filesystem, then simply use
    rename. Otherwise, copy source to the destination and then remove
    source.
    
    @type  source: string
    @param source: Source file or directory (file or directory to move).
    @type  destination: string
    @param destination: Destination file or directory (where to move).
    @rtype:  boolean
    @return: True if the operation is successful, False otherwise.
    '''
    LOG_INFO('Move: %s -> %s' % (source, destination))
    try:
        shutil.move(source, destination)
        return True
    except:
        LOG_EXCEPTION('Failed to Move: %s -> %s' % (source, destination))
        return False


def rmfile(path):
    '''Delete a file
    
    @type  path: string
    @param path: Path to the file that needs to be deleted.
    @rtype:  boolean
    @return: True if the operation is successful, False otherwise.
    '''
    LOG_INFO('rmfile: %s' % path)
    try:
        os.remove(path)
        return True
    except Exception, e:
        LOG_ERROR('rmfile: %s failed! Error: %s' % (path, e))
        return False


def rmtree(path):
    '''Recursively delete a directory tree.

    @type  path: string
    @param path: Path to the directory that needs to be deleted.
    @rtype:  boolean
    @return: True if the operation is successful, False otherwise.
    '''
    LOG_INFO('rmtree: %s' % path)
    try:
        shutil.rmtree(path)
        return True
    except Exception, e:
        LOG_ERROR('rmtree: %s failed! Error: %s' % (path, e))
        return False


def remove(path):
    '''Delete a file or directory
    
    @type  path: string
    @param path: Path to the file or directory that needs to be deleted.
    @rtype:  boolean
    @return: True if the operation is successful, False otherwise.
    '''
    if os.path.isdir(path):
        return rmtree(path)
    else:
        return rmfile(path)
