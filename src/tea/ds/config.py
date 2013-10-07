from __future__ import print_function, unicode_literals

__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '25 July 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import os
import io
import json
import copy
import logging
import functools
import threading
from tea import shutil
from tea.utils import six
try:
    import yaml
    has_yaml = True
except ImportError:
    has_yaml = False


logger = logging.getLogger(__name__)


class ConfigError(Exception):
    pass


def locked(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        with self.lock:
            return func(self, *args, **kwargs)
    return wrapper


def _get_format(filename):
    return os.path.splitext(filename)[-1].lower()[1:]


def _ensure_exists(filename, encoding='utf-8'):
    """Ensures that the configuration file exists and that it produces a
    correct empty configuration.
    """
    filename = os.path.abspath(filename)
    if not os.path.isfile(filename):
        dirname = os.path.dirname(filename)
        if not os.path.isdir(dirname):
            shutil.mkdir(dirname)
        with io.open(filename, 'w', encoding=encoding) as f:
            fmt = _get_format(filename)
            if fmt in (Config.JSON, Config.YAML):
                f.write('{}')
            f.write('\n')


class Config(object):
    """Configuration class"""
    DICT = 'dict'
    JSON = 'json'
    YAML = 'yaml'

    ensure_exists = staticmethod(_ensure_exists)

    def __init__(self, filename=None, data=None, fmt=None, encoding='utf-8',
                 autosave=True):
        self.lock = threading.Lock()
        self.encoding = encoding
        self.autosave = autosave
        if filename is not None:
            self.filename = os.path.abspath(filename)
            self.format = (fmt if fmt is not None
                           else _get_format(self.filename))
            self.data = self._read_file()
        else:
            self.filename = filename
            self.format = Config.JSON if fmt is None else fmt
            if isinstance(data, dict):
                self.format = Config.DICT
                self.data = copy.deepcopy(data)
            elif isinstance(data, six.string_types):
                self.data = self._read_string(data)
            else:
                self.data = {}

    def _read_file(self):
        try:
            if self.format == Config.JSON:
                with io.open(self.filename, 'r+b') as f:
                    return json.load(f, encoding=self.encoding)
            elif self.format == Config.YAML:
                if has_yaml:
                    with io.open(self.filename, 'r',
                                 encoding=self.encoding) as f:
                        return yaml.safe_load(f)
                else:
                    logger.error('YAML is not installed.')
                    return {}
            else:
                logger.error('Unsupported configuration format: %s',
                             self.format)
                return {}
        except Exception as e:
            logger.error('Failed to load file "%s" in format "%s". %s',
                         self.filename, self.format, e)
            return {}

    def _read_string(self, data):
        try:
            if isinstance(data, bytes):
                data = data.decode(self.encoding)
            if self.format == Config.JSON:
                return json.loads(data)
            elif self.format == Config.YAML:
                if has_yaml:
                    return yaml.safe_load(data)
                else:
                    logger.error('YAML is not installed.')
                    return {}
            else:
                logger.error('Unsupported configuration format: %s',
                             self.format)
                return {}
        except:
            logger.exception('Failed to load data in format "%s"', self.format)
            return {}

    def save(self):
        if self.filename is not None:
            if self.format == Config.JSON:
                with io.open(self.filename, 'w+b') as f:
                    json.dump(self.data, f, indent=2, encoding=self.encoding)
            elif self.format == Config.YAML:
                if has_yaml:
                    with io.open(self.filename, 'w',
                                 encoding=self.encoding) as f:
                        yaml.safe_dump(self.data, f, default_flow_style=False)
                else:
                    logger.error('YAML is not installed,')
            else:
                logger.error('Unsupported configuration format: %s',
                             self.format)

    def __get(self, var, create=False):
        current = self.data
        for part in var.split('.'):
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
                except:
                    raise IndexError(var)
            else:
                raise KeyError(var)
        return current

    def __set(self, var, value):
        if '.' in var:
            path, _, item = var.rpartition('.')
            current = self.__get(path, create=True)
        else:
            current = self.data
            item = var
        if isinstance(current, dict):
            current[item] = value
        elif isinstance(current, list):
            item = int(item, 10)
            current[item] = value
        if self.autosave:
            self.save()

    def __del(self, var):
        if '.' in var:
            path, _, item = var.rpartition('.')
            current = self.__get(path)
        else:
            current = self.data
            item = var
        if isinstance(current, dict):
            del current[item]
        elif isinstance(current, list):
            item = int(item, 10)
            current.pop(item)
        if self.autosave:
            self.save()

    @locked
    def keys(self):
        """Returns a set of top level keys in this configuration"""
        return set(self.data.keys())

    @locked
    def __getitem__(self, item):
        """Unsafe version, may raise KeyError or IndexError"""
        return self.__get(item)

    @locked
    def __setitem__(self, item, value):
        return self.__set(item, value)

    @locked
    def __delitem__(self, item):
        """Unsafe version, may raise KeyError or IndexError"""
        return self.__del(item)

    @locked
    def get(self, var, default=None):
        """Safe version which always returns a default value"""
        try:
            return self.__get(var)
        except (KeyError, IndexError):
            return default

    @locked
    def set(self, var, value):
        return self.__set(var, value)

    @locked
    def delete(self, var):
        """Safe version, never, raises an error"""
        try:
            return self.__del(var)
        except:
            pass

    @locked
    def insert(self, var, value, index=None):
        """Inserts at the index, and if the index is not provided
        appends to the end of the list
        """
        current = self.__get(var)
        if not isinstance(current, list):
            raise KeyError('%s: is not a list' % var)
        if index is None:
            current.append(value)
        else:
            current.insert(index, value)
        if self.autosave:
            self.save()

    def __repr__(self):
        return ('Config(filename="%(filename)s", format="%(format)s", '
                'encoding="%(encoding)s", autosave=%(autosave)s)' %
                self.__dict__)


class MultiConfig(object):
    """Base class for configuration management"""

    ensure_exists = staticmethod(_ensure_exists)

    def __init__(self, filename=None, data=None, fmt=None, encoding='utf-8',
                 autosave=True):
        self.lock = threading.Lock()
        self.__configs = []
        self.attach(filename, data, fmt, encoding, autosave)

    @locked
    def attach(self, filename=None, data=None, fmt=None, encoding='utf-8',
               autosave=True, index=None):
        config = Config(filename, data, fmt, encoding, autosave)
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
        """Returns a merged set of top level keys from all the configuration
        files
        """
        s = set()
        for config in self.__configs:
            s |= config.keys()
        return s

    @locked
    def __getitem__(self, item):
        """Unsafe version, may raise KeyError or IndexError"""
        return self.__get(item)

    @locked
    def __setitem__(self, item, value):
        return self.__set(item, value)

    @locked
    def __delitem(self, item):
        """Unsafe version, may raise KeyError or IndexError"""
        self.__del(item)

    @locked
    def get(self, var, default=None):
        """Safe version always returns a default value"""
        try:
            return self.__get(var)
        except (KeyError, IndexError):
            return default

    @locked
    def set(self, var, value):
        return self.__set(var, value)

    @locked
    def delete(self, var):
        """Safe version, never raises an error"""
        try:
            self.__del(var)
        except (KeyError, IndexError):
            pass

    @locked
    def insert(self, var, value, index=None):
        self.current.insert(var, value, index)

    def __repr__(self):
        return ('MultiConfig(\n  %s\n)' %
                (',\n  '.join(reversed(map(repr, self._configs)))))
