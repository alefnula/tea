import os
import io
import json
import copy
import logging
import functools
import threading
from tea import shell


logger = logging.getLogger(__name__)


def locked(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        with self.lock:
            return func(self, *args, **kwargs)

    return wrapper


class Config(object):
    """Configuration class."""

    DICT = "dict"
    JSON = "json"

    def __init__(
        self,
        filename=None,
        data=None,
        fmt=None,
        encoding="utf-8",
        auto_save=True,
    ):
        self.lock = threading.Lock()
        self.encoding = encoding
        self.auto_save = auto_save
        if filename is not None:
            self.filename = os.path.abspath(filename)
            self.fmt = (
                fmt
                if fmt is not None
                else os.path.splitext(self.filename)[-1].lower()[1:]
            )
            self.data = self._read_file()
        else:
            self.filename = filename
            self.fmt = Config.JSON if fmt is None else fmt
            if isinstance(data, dict):
                self.fmt = Config.DICT
                self.data = copy.deepcopy(data)
            elif isinstance(data, (str, bytes)):
                self.data = self._read_string(data)
            else:
                self.data = {}

    def _read_file(self):
        if not os.path.isfile(self.filename):
            logger.warning(
                'Configuration file "%s" does not exist', self.filename
            )
            return {}
        try:
            if self.fmt == Config.JSON:
                with io.open(self.filename, "r", encoding=self.encoding) as f:
                    return json.loads(f.read())
            else:
                logger.error("Unsupported configuration format: %s", self.fmt)
                return {}
        except Exception as e:
            logger.error(
                'Failed to load file "%s" in format "%s". %s',
                self.filename,
                self.fmt,
                e,
            )
            return {}

    def _read_string(self, data):
        try:
            if isinstance(data, bytes):
                data = data.decode(self.encoding)
            if self.fmt == Config.JSON:
                return json.loads(data)
            else:
                logger.error("Unsupported configuration format: %s", self.fmt)
                return {}
        except Exception as e:
            logger.error('Failed to load data in format "%s". %s', self.fmt, e)
            return {}

    def save(self):
        if self.filename is not None:
            dirname = os.path.abspath(os.path.dirname(self.filename))
            if not os.path.isdir(dirname):
                shell.mkdir(dirname)
            if self.fmt == Config.JSON:
                with io.open(self.filename, "w", encoding=self.encoding) as f:
                    f.write(json.dumps(self.data, indent=2))
            else:
                logger.error("Unsupported configuration format: %s", self.fmt)

    def __get(self, var, create=False):
        current = self.data
        for part in var.split("."):
            if isinstance(current, dict):
                if part in current:
                    current = current[part]
                elif create:
                    current = current.setdefault(part, {})
                else:
                    raise KeyError(var)
            elif isinstance(current, list):
                try:
                    part = int(part, 10)
                    current = current[part]
                except Exception:
                    raise IndexError(var)
            else:
                raise KeyError(var)
        return current

    def __set(self, var, value):
        if "." in var:
            path, _, item = var.rpartition(".")
            current = self.__get(path, create=True)
        else:
            current = self.data
            item = var
        if isinstance(current, dict):
            current[item] = value
        elif isinstance(current, list):
            item = int(item, 10)
            current[item] = value
        if self.auto_save:
            self.save()

    def __del(self, var):
        if "." in var:
            path, _, item = var.rpartition(".")
            current = self.__get(path)
        else:
            current = self.data
            item = var
        if isinstance(current, dict):
            del current[item]
        elif isinstance(current, list):
            item = int(item, 10)
            current.pop(item)
        if self.auto_save:
            self.save()

    @locked
    def keys(self):
        """Return a set of top level keys in this configuration."""
        return set(self.data.keys())

    @locked
    def __getitem__(self, item):
        """Return a value from configuration.

        Unsafe version, may raise KeyError or IndexError.
        """
        return self.__get(item)

    @locked
    def __setitem__(self, item, value):
        return self.__set(item, value)

    @locked
    def __delitem__(self, item):
        """Delete an item from configuration.

        Unsafe version, may raise KeyError or IndexError.
        """
        return self.__del(item)

    @locked
    def __contains__(self, item):
        try:
            self.__get(item)
            return True
        except (KeyError, IndexError):
            return False

    @locked
    def get(self, var, default=None):
        """Return a value from configuration.

        Safe version which always returns a default value if the value is not
        found.
        """
        try:
            return self.__get(var)
        except (KeyError, IndexError):
            return default

    @locked
    def set(self, var, value):
        return self.__set(var, value)

    @locked
    def delete(self, var):
        """Delete an item from configuration.

        Safe version, never, raises an error.
        """
        try:
            return self.__del(var)
        except Exception:
            pass

    @locked
    def insert(self, var, value, index=None):
        """Insert at the index.

        If the index is not provided appends to the end of the list.
        """
        current = self.__get(var)
        if not isinstance(current, list):
            raise KeyError("%s: is not a list" % var)
        if index is None:
            current.append(value)
        else:
            current.insert(index, value)
        if self.auto_save:
            self.save()

    def __repr__(self):
        return (
            'Config(filename="%(filename)s", format="%(fmt)s", '
            'encoding="%(encoding)s", auto_save=%(auto_save)s)' % self.__dict__
        )


class MultiConfig(object):
    """Base class for configuration management."""

    def __init__(
        self,
        filename=None,
        data=None,
        fmt=None,
        encoding="utf-8",
        auto_save=True,
    ):
        self.lock = threading.Lock()
        self.__configs = []
        self.attach(filename, data, fmt, encoding, auto_save)

    @locked
    def attach(
        self,
        filename=None,
        data=None,
        fmt=None,
        encoding="utf-8",
        auto_save=True,
        index=None,
    ):
        config = Config(filename, data, fmt, encoding, auto_save)
        if index is None:
            self.__configs.insert(0, config)
        else:
            self.__configs.insert(index, config)

    @locked
    def detach(self, index=None):
        if index is None:
            self.__configs.pop(0)
        else:
            self.__configs.pop(index)

    @property
    def current(self):
        return self.__configs[0]

    def __get(self, var):
        for config in self.__configs:
            try:
                return config[var]
            except (KeyError, IndexError):
                pass
        raise KeyError(var)

    def __set(self, var, value):
        return self.current.set(var, value)

    def __del(self, var):
        # It has to keep track if it found a value in any of the configuration
        # files. If the value is found it won't raise and error, if it is not
        # found in any configuration file, it will raise a KeyError
        found = []
        for config in self.__configs:
            try:
                del config[var]
                found.append(True)
            except (KeyError, IndexError):
                found.append(True)
        if not any(found):
            raise KeyError(var)

    @locked
    def keys(self):
        """Return a merged set of top level keys from all configurations."""
        s = set()
        for config in self.__configs:
            s |= config.keys()
        return s

    @locked
    def __getitem__(self, item):
        """Return a value from configuration.

        Unsafe version, may raise KeyError or IndexError.
        """
        return self.__get(item)

    @locked
    def __setitem__(self, item, value):
        return self.__set(item, value)

    @locked
    def __delitem__(self, item):
        """Delete an item from configuration.

        Unsafe version, may raise KeyError or IndexError.
        """
        self.__del(item)

    @locked
    def __contains__(self, item):
        try:
            self.__get(item)
            return True
        except (KeyError, IndexError):
            return False

    @locked
    def get(self, var, default=None):
        """Return a value from configuration.

        Safe version which always returns a default value if the value is not
        found.
        """
        try:
            return self.__get(var)
        except (KeyError, IndexError):
            return default

    @locked
    def set(self, var, value):
        return self.__set(var, value)

    @locked
    def delete(self, var):
        """Delete an item from configuration.

        Safe version, never, raises an error.
        """
        try:
            self.__del(var)
        except (KeyError, IndexError):
            pass

    @locked
    def insert(self, var, value, index=None):
        self.current.insert(var, value, index)

    def __repr__(self):
        return "MultiConfig(\n  %s\n)" % (
            ",\n  ".join(reversed(map(repr, self.__configs)))
        )
