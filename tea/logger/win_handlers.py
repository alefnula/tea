__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '27 November 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import os
import logging
from .win_file import WindowsFile


class FileHandler(logging.StreamHandler):
    """A handler class which writes formatted logging records to disk
    files.
    """
    def __init__(self, filename, mode='a', encoding=None):
        """Open the specified file and use it as the stream for logging."""
        stream = WindowsFile(filename, mode, encoding)
        logging.StreamHandler.__init__(self, stream)
        #keep the absolute path, otherwise derived classes which use this
        #may come a cropper when the current directory changes
        self.baseFilename = os.path.abspath(filename)
        self.mode = mode

    def close(self):
        """Closes the stream."""
        self.flush()
        self.stream.close()
        logging.StreamHandler.close(self)


class BaseRotatingHandler(FileHandler):
    """Base class for handlers that rotate log files at a certain point.

    Not meant to be instantiated directly. Instead, use
    :ref:`RotatingFileHandler` or :ref:`TimedRotatingFileHandler`.
    """
    def __init__(self, filename, mode, encoding=None):
        """Use the specified filename for streamed logging"""
        FileHandler.__init__(self, filename, mode, encoding)
        self.mode = mode
        self.encoding = encoding

    def emit(self, record):
        """Emit a record.

        Output the record to the file, catering for rollover as described
        in doRollover().
        """
        try:
            if self.shouldRollover(record):
                self.doRollover()
            FileHandler.emit(self, record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class RotatingFileHandler(BaseRotatingHandler):
    """Handler for logging to a set of files, which switches from one file
    to the next when the current file reaches a certain size.
    """
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0,
                 encoding=None):
        """Open the specified file and use it as the stream for logging.

        By default, the file grows indefinitely. You can specify particular
        values of maxBytes and backupCount to allow the file to rollover at
        a predetermined size.

        Rollover occurs whenever the current log file is nearly maxBytes in
        length. If backupCount is >= 1, the system will successively create
        new files with the same pathname as the base file, but with extensions
        ".1", ".2" etc. appended to it. For example, with a backupCount of 5
        and a base file name of "app.log", you would get "app.log",
        "app.log.1", "app.log.2", ... through to "app.log.5". The file being
        written to is always "app.log" - when it gets filled up, it is closed
        and renamed to "app.log.1", and if files "app.log.1", "app.log.2" etc.
        exist, then they are renamed to "app.log.2", "app.log.3" etc.
        respectively.

        If maxBytes is zero, rollover never occurs.
        """
        if maxBytes > 0:
            mode = 'a'  # doesn't make sense otherwise!
        BaseRotatingHandler.__init__(self, filename, mode, encoding)
        self.maxBytes = maxBytes
        self.backupCount = backupCount

    def doRollover(self):
        """Do a rollover, as described in __init__()."""
        self.stream.close()
        try:
            if self.backupCount > 0:
                tmp_location = '%s.0' % self.baseFilename
                os.rename(self.baseFilename, tmp_location)
                for i in range(self.backupCount - 1, 0, -1):
                    sfn = '%s.%d' % (self.baseFilename, i)
                    dfn = '%s.%d' % (self.baseFilename, i + 1)
                    if os.path.exists(sfn):
                        if os.path.exists(dfn):
                            os.remove(dfn)
                        os.rename(sfn, dfn)
                dfn = self.baseFilename + ".1"
                if os.path.exists(dfn):
                    os.remove(dfn)
                os.rename(tmp_location, dfn)
        except:
            pass
        finally:
            self.stream = WindowsFile(self.baseFilename, 'a', self.encoding)

    def shouldRollover(self, record):
        """Determine if rollover should occur.

        Basically, see if the supplied record would cause the file to exceed
        the size limit we have.
        """
        if self.maxBytes > 0:  # are we rolling over?
            msg = "%s\n" % self.format(record)
            self.stream.seek(0, 2)  # due to non-posix-compliant win feature
            if self.stream.tell() + len(msg) >= self.maxBytes:
                return 1
        return 0
