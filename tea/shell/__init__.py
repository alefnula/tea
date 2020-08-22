"""Module mimics some of the behaviors of the builtin :mod:`shutil`.

It adds logging to all operations and abstracting some other useful shell
commands (functions).
"""

import os
import io
import glob
import shlex
import shutil
import fnmatch
import logging
import contextlib


logger = logging.getLogger(__name__)


def split(s, posix=True):
    """Split the string s using shell-like syntax.

    Args:
        s (str): String to split
        posix (bool): Use posix split

    Returns:
        list of str: List of string parts
    """
    if isinstance(s, bytes):
        s = s.decode("utf-8")
    return shlex.split(s, posix=posix)


def search(path, matcher="*", dirs=False, files=True):
    """Recursive search function.

    Args:
        path (str): Path to search recursively
        matcher (str or callable): String pattern to search for or function
            that returns True/False for a file argument
        dirs (bool): if True returns directories that match the pattern
        files(bool): if True returns files that match the patter

    Yields:
        str: Found files and directories
    """
    if callable(matcher):

        def fnmatcher(items):
            return list(filter(matcher, items))

    else:

        def fnmatcher(items):
            return fnmatch.filter(items, matcher)

    for root, directories, filenames in os.walk(os.path.abspath(path)):
        to_match = []
        if dirs:
            to_match.extend(directories)
        if files:
            to_match.extend(filenames)
        for item in fnmatcher(to_match):
            yield os.path.join(root, item)


def chdir(directory):
    """Change the current working directory.

    Args:
        directory (str): Directory to go to.
    """
    directory = os.path.abspath(directory)
    logger.info("chdir -> %s" % directory)
    try:
        if not os.path.isdir(directory):
            logger.error(
                "chdir -> %s failed! Directory does not exist!", directory
            )
            return False
        os.chdir(directory)
        return True
    except Exception as e:
        logger.error("chdir -> %s failed! %s" % (directory, e))
        return False


@contextlib.contextmanager
def goto(directory, create=False):
    """Context object for changing directory.

    Args:
        directory (str): Directory to go to.
        create (bool): Create directory if it doesn't exists.

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
        logger.info("goto -> %s", directory)
        os.chdir(directory)
        try:
            yield True
        finally:
            logger.info("goto <- %s", directory)
            os.chdir(current)
    else:
        logger.info(
            "goto(%s) - directory does not exist, or cannot be " "created.",
            directory,
        )
        yield False


def mkdir(path, mode=0o755, delete=False):
    """Make a directory.

    Create a leaf directory and all intermediate ones.
    Works like ``mkdir``, except that any intermediate path segment (not just
    the rightmost) will be created if it does not exist. This is recursive.

    Args:
        path (str): Directory to create
        mode (int): Directory mode
        delete (bool): Delete directory/file if exists

    Returns:
        bool: True if succeeded else False
    """
    logger.info("mkdir: %s" % path)
    if os.path.isdir(path):
        if not delete:
            return True
        if not remove(path):
            return False
    try:
        os.makedirs(path, mode)
        return True
    except Exception:
        logger.exception("Failed to mkdir: %s" % path)
        return False


def __create_destdir(destination):
    destdir = os.path.dirname(destination)
    if not os.path.isdir(destdir):
        if not mkdir(destdir):
            raise Exception('Failed to create "%s"' % destdir)


def __copyfile(source, destination):
    """Copy data and mode bits ("cp source destination").

    The destination may be a directory.

    Args:
        source (str): Source file (file to copy).
        destination (str): Destination file or directory (where to copy).

    Returns:
        bool: True if the operation is successful, False otherwise.
    """
    logger.info("copyfile: %s -> %s" % (source, destination))
    try:
        __create_destdir(destination)
        shutil.copy(source, destination)
        return True
    except Exception as e:
        logger.error(
            "copyfile: %s -> %s failed! Error: %s", source, destination, e
        )
        return False


def __copyfile2(source, destination):
    """Copy data and all stat info ("cp -p source destination").

    The destination may be a directory.

    Args:
        source (str): Source file (file to copy).
        destination (str): Destination file or directory (where to copy).

    Returns:
        bool: True if the operation is successful, False otherwise.
    """
    logger.info("copyfile2: %s -> %s" % (source, destination))
    try:
        __create_destdir(destination)
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        logger.error(
            "copyfile2: %s -> %s failed! Error: %s", source, destination, e
        )
        return False


def __copytree(source, destination, symlinks=False):
    """Copy a directory tree recursively using copy2().

    The destination directory must not already exist.

    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied.

    Args:
        source (str): Source directory (directory to copy).
        destination (str): Destination directory (where to copy).
        symlinks (bool): Follow symbolic links.

    Returns:
        bool: True if the operation is successful, False otherwise.
    """
    logger.info("copytree: %s -> %s" % (source, destination))
    try:
        __create_destdir(destination)
        shutil.copytree(source, destination, symlinks)
        return True
    except Exception as e:
        logger.exception(
            "copytree: %s -> %s failed! Error: %s", source, destination, e
        )
        return False


def copy(source, destination):
    """Copy file or directory.

    Args:
        source (str): Source file or directory
        destination (str): Destination file or directory (where to copy).

    Returns:
        bool: True if the operation is successful, False otherwise.
    """
    if os.path.isdir(source):
        return __copytree(source, destination)
    else:
        return __copyfile2(source, destination)


def gcopy(pattern, destination):
    """Copy all file found by glob.glob(pattern) to destination directory.

    Args:
        pattern (str): Glob pattern
        destination (str): Path to the destination directory.

    Returns:
        bool: True if the operation is successful, False otherwise.
    """
    for item in glob.glob(pattern):
        if not copy(item, destination):
            return False
    return True


def move(source, destination):
    """Move a file or directory (recursively) to another location.

    If the destination is on our current file system, then simply use
    rename. Otherwise, copy source to the destination and then remove
    source.

    Args:
        source (str): Source file or directory (file or directory to move).
        destination (str): Destination file or directory (where to move).

    Returns:
        bool: True if the operation is successful, False otherwise.
    """
    logger.info("Move: %s -> %s" % (source, destination))
    try:
        __create_destdir(destination)
        shutil.move(source, destination)
        return True
    except Exception:
        logger.exception("Failed to Move: %s -> %s" % (source, destination))
        return False


def gmove(pattern, destination):
    """Move all file found by glob.glob(pattern) to destination directory.

    Args:
        pattern (str): Glob pattern
        destination (str): Path to the destination directory.

    Returns:
        bool: True if the operation is successful, False otherwise.
    """
    for item in glob.glob(pattern):
        if not move(item, destination):
            return False
    return True


def __rmfile(path):
    """Delete a file.

    Args:
        path (str): Path to the file that needs to be deleted.

    Returns:
        bool: True if the operation is successful, False otherwise.
    """
    logger.info("rmfile: %s" % path)
    try:
        os.remove(path)
        return True
    except Exception as e:
        logger.error("rmfile: %s failed! Error: %s" % (path, e))
        return False


def __rmtree(path):
    """Recursively delete a directory tree.

    Args:
        path (str): Path to the directory that needs to be deleted.

    Returns:
        bool: True if the operation is successful, False otherwise.
    """
    logger.info("rmtree: %s" % path)
    try:
        shutil.rmtree(path)
        return True
    except Exception as e:
        logger.error("rmtree: %s failed! Error: %s" % (path, e))
        return False


def remove(path):
    """Delete a file or directory.

    Args:
        path (str): Path to the file or directory that needs to be deleted.

    Returns:
        bool: True if the operation is successful, False otherwise.
    """
    if os.path.isdir(path):
        return __rmtree(path)
    else:
        return __rmfile(path)


def gremove(pattern):
    """Remove all file found by glob.glob(pattern).

    Args:
        pattern (str): Pattern of files to remove
    Returns:
        bool: True if the operation is successful, False otherwise.
    """
    for item in glob.glob(pattern):
        if not remove(item):
            return False
    return True


def read(path, encoding="utf-8"):
    """Read the content of the file.

    Args:
        path (str): Path to the file
        encoding (str): File encoding. Default: utf-8

    Returns:
        str: File content or empty string if there was an error
    """
    try:
        with io.open(path, encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.error("read: %s failed. Error: %s", path, e)
        return ""


def touch(path, content="", encoding="utf-8", overwrite=False):
    """Create a file at the given path if it does not already exists.

    Args:
        path (str): Path to the file.
        content (str): Optional content that will be written in the file.
        encoding (str): Encoding in which to write the content.
            Default: ``utf-8``
        overwrite (bool): Overwrite the file if exists.

    Returns:
        bool: True if the operation is successful, False otherwise.
    """
    path = os.path.abspath(path)
    if not overwrite and os.path.exists(path):
        logger.warning('touch: "%s" already exists', path)
        return False
    try:
        logger.info("touch: %s", path)
        with io.open(path, "wb") as f:
            if not isinstance(content, bytes):
                content = content.encode(encoding)
            f.write(content)
        return True
    except Exception as e:
        logger.error("touch: %s failed. Error: %s", path, e)
        return False
