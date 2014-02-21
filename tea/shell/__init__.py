"""This module mimics some of the behaviors of the builtin :mod:`shutil`
module, adding logging to all operations and abstracting some other useful
shell commands (functions).
"""

__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '27 November 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import os
import io
import glob
import shlex
import shutil
import fnmatch
import logging
import contextlib
from tea.utils import six

logger = logging.getLogger(__name__)


def split(s, posix=True):
    """Split the string s using shell-like syntax"""
    if isinstance(s, six.binary_type):
        s = s.decode('utf-8')
    return shlex.split(s, posix=posix)


def search(path, matcher='*', dirs=False, files=True):
    """Recursive search function.

    :param path: path to search recursively
    :param matcher: string pattern to search for or function that returns
        True/False for a file argument
    :param dirs: if True returns also directories that match the pattern
    """
    if callable(matcher):
        fnmatcher = lambda items: list(filter(matcher, items))
    else:
        fnmatcher = lambda items: fnmatch.filter(items, matcher)
    for root, directories, filenames in os.walk(os.path.abspath(path)):
        items = []
        if dirs:
            items.extend(directories)
        if files:
            items.extend(filenames)
        for item in fnmatcher(items):
            yield os.path.join(root, item)


def chdir(directory):
    """Change the current working directory"""
    directory = os.path.abspath(directory)
    logger.info('chdir -> %s' % directory)
    try:
        if not os.path.isdir(directory):
            logger.error('chdir -> %s failed! Directory does not exist!',
                         directory)
            return False
        os.chdir(directory)
        return True
    except Exception as e:
        logger.error('chdir -> %s failed! %s' % (directory, e))
        return False


@contextlib.contextmanager
def goto(directory, create=False):
    """Context object for changing directory.

    Usage::

        >>> with goto(directory) as ok:
        ...     if not ok:
        ...         print 'Error'
        ...     else:
        ...         print 'All OK'
    """

    current = os.getcwd()
    directory = os.path.abspath(directory)

    if os.path.isdir(directory) or (create and mkdir(directory)):
        logger.info('goto -> %s', directory)
        os.chdir(directory)
        try:
            yield True
        finally:
            logger.info('goto <- %s', directory)
            os.chdir(current)
    else:
        logger.info('goto(%s) - directory does not exist, or cannot be '
                    'created.', directory)
        yield False


def mkdir(path, mode=0o777, delete=False):
    """mkdir(path [, mode=0777])

    Create a leaf directory and all intermediate ones.
    Works like mkdir, except that any intermediate path segment (not
    just the rightmost) will be created if it does not exist.  This is
    recursive.

    :param str path: directory to create
    :param int mode: directory mode
    :param bool delete: delete directory/file if exists
    :rtype: :obj:`bool`
    :return: True if succeeded else False
    """
    logger.info('mkdir: %s' % path)
    if os.path.isdir(path):
        if not delete:
            return True
        if not remove(path):
            return False
    try:
        os.makedirs(path, mode)
        return True
    except:
        logger.exception('Failed to mkdir: %s' % path)
        return False


def __create_destdir(destination):
    destdir = os.path.dirname(destination)
    if not os.path.isdir(destdir):
        if not mkdir(destdir):
            raise Exception('Failed to create "%s"' % destdir)


def __copyfile(source, destination):
    """Copy data and mode bits ("cp source destination").

    The destination may be a directory.

    :param str source: Source file (file to copy).
    :param str destination: Destination file or directory (where to copy).
    :rtype: :obj:`bool`
    :return: True if the operation is successful, False otherwise.
    """
    logger.info('copyfile: %s -> %s' % (source, destination))
    try:
        __create_destdir(destination)
        shutil.copy(source, destination)
        return True
    except Exception as e:
        logger.error('copyfile: %s -> %s failed! Error: %s',
                     source, destination, e)
        return False


def __copyfile2(source, destination):
    """Copy data and all stat info ("cp -p source destination").

    The destination may be a directory.

    :param str source: Source file (file to copy).
    :param str destination: Destination file or directory (where to copy).
    :rtype: :obj:`bool`
    :return: True if the operation is successful, False otherwise.
    """
    logger.info('copyfile2: %s -> %s' % (source, destination))
    try:
        __create_destdir(destination)
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        logger.error('copyfile2: %s -> %s failed! Error: %s',
                     source, destination, e)
        return False


def __copytree(source, destination, symlinks=False):
    """Recursively copy a directory tree using copy2().

    The destination directory must not already exist.

    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied.

    :param str source: Source directory (directory to copy).
    :param str destination: Destination directory (where to copy).
    :param bool symlinks: Follow symbolic links.
    :rtype: :obj:`bool`
    :return: True if the operation is successful, False otherwise.
    """
    logger.info('copytree: %s -> %s' % (source, destination))
    try:
        __create_destdir(destination)
        shutil.copytree(source, destination, symlinks)
        return True
    except Exception as e:
        logger.exception('copytree: %s -> %s failed! Error: %s',
                         source, destination, e)
        return False


def copy(source, destination):
    """Copy file or directory"""
    if os.path.isdir(source):
        return __copytree(source, destination)
    else:
        return __copyfile2(source, destination)


def gcopy(pattern, destination):
    """Copy all file found by glob.glob(pattern) to destination directory"""
    for item in glob.glob(pattern):
        if not copy(item, destination):
            return False
    return True


def move(source, destination):
    """Recursively move a file or directory to another location.

    If the destination is on our current file system, then simply use
    rename. Otherwise, copy source to the destination and then remove
    source.

    :param str source: Source file or directory (file or directory to move).
    :param str destination: Destination file or directory (where to move).
    :rtype: :obj:`bool`
    :return: True if the operation is successful, False otherwise.
    """
    logger.info('Move: %s -> %s' % (source, destination))
    try:
        __create_destdir(destination)
        shutil.move(source, destination)
        return True
    except:
        logger.exception('Failed to Move: %s -> %s' % (source, destination))
        return False


def gmove(pattern, destination):
    """Move all file found by glob.glob(pattern) to destination directory"""
    for item in glob.glob(pattern):
        if not move(item, destination):
            return False
    return True


def __rmfile(path):
    """Delete a file

    :param str path: Path to the file that needs to be deleted.
    :rtype: :obj:`bool`
    :return: True if the operation is successful, False otherwise.
    """
    logger.info('rmfile: %s' % path)
    try:
        os.remove(path)
        return True
    except Exception as e:
        logger.error('rmfile: %s failed! Error: %s' % (path, e))
        return False


def __rmtree(path):
    """Recursively delete a directory tree.

    :param str path: Path to the directory that needs to be deleted.
    :rtype: :obj:`bool`
    :return: True if the operation is successful, False otherwise.
    """
    logger.info('rmtree: %s' % path)
    try:
        shutil.rmtree(path)
        return True
    except Exception as e:
        logger.error('rmtree: %s failed! Error: %s' % (path, e))
        return False


def remove(path):
    """Delete a file or directory

    :param str path: Path to the file or directory that needs to be deleted.
    :rtype: :obj:`bool`
    :return: True if the operation is successful, False otherwise.
    """
    if os.path.isdir(path):
        return __rmtree(path)
    else:
        return __rmfile(path)


def gremove(pattern):
    """Remove all file found by glob.glob(pattern)

    :param str pattern: Pattern of files to remove
    """
    for item in glob.glob(pattern):
        if not remove(item):
            return False
    return True


def touch(path, content='', encoding='utf-8'):
    """Create a file at the given path if it does not already exists.

    :param str path: Path to the file.
    :param str content: Optional content that will be written in the file.
    :param str encoding: Encoding in which to write the content.
        Default: ``utf-8``
    """
    path = os.path.abspath(path)
    if os.path.exists(path):
        logger.warning('touch: "%s" already exists', path)
        return False
    try:
        logger.info('touch: %s', path)
        with io.open(path, 'wb') as f:
            if not isinstance(content, six.binary_type):
                content = content.encode(encoding)
            f.write(content)
        return True
    except Exception as e:
        logger.error('touch: %s failed. Error: %s', path, e)
        return False
