from __future__ import print_function

__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '25 July 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import os
import io
import json
import copy
import logging
try:
    import yaml
    has_yaml = True
except ImportError:
    has_yaml = False

if str is bytes:
    bytes_type = str
    unicode_type = unicode
else:
    bytes_type = bytes
    unicode_type = str


logger = logging.getLogger(__name__)


class ConfigError(Exception):
    pass


class Config(object):
    '''Configuration class'''
    JSON = '.json'
    YAML = '.yaml'
    
    class NotFound(Exception):
        pass
    
    def __init__(self, filename=None, data=None, fmt=None, encoding='utf-8', autosave=True):
        self.encoding = encoding
        self.autosave = autosave
        if filename is not None:
            self.filename = os.path.abspath(filename)
            self.format = fmt if fmt is not None else os.path.splitext(self.filename)[-1].lower()
            self.data = self._read_file()
        else:
            self.filename = filename
            self.format   = Config.JSON if fmt is None else fmt
            if isinstance(data, dict):
                self.data = copy.deepcopy(data)
            elif isinstance(data, (bytes_type, unicode_type)):
                self.data = self._read_string(data)
            else:
                self.data = {}
        
    def _read_file(self):
        try:
            if self.format == Config.JSON:
                with io.open(self.filename, 'r+b') as f:
                    return json.load(f, encoding=self.encodign)
            elif self.format == Config.YAML:
                if has_yaml:
                    with io.open(self.filename, 'r', encoding=self.encodign) as f:
                        return yaml.safe_load(f)
                else:
                    logger.error('YAML is not installed, cannot load .yaml files.')
                    return {}
            else:
                logger.error('Unsupported configuration format: %s', self.format)
                return {}
        except:
            logger.exception('Failed to load file "%s" in format "%s"', self.filename, self.format)
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
                    logger.error('YAML is not installed, cannot load .yaml files.')
                    return {}
            else:
                logger.error('Unsupported configuration format: %s', self.format)
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
                    with io.open(self.filename, 'w', encoding=self.encoding) as f:
                        yaml.safe_dump(self.data, f, default_flow_style=False)
                else:
                    logger.error('YAML is not installed, cannot save .yaml files.')
            else:
                logger.error('Unsupported configuration format: %s', self.format)

    def _get(self, var, create=False):
        current = self.data
        for part in var.split('.'):
            if isinstance(current, dict):
                if part in current:
                    current = current[part]
                elif create:
                    current = current.setdefault(part, {})
                else:
                    raise Config.NotFound(var)
            elif isinstance(current, list):
                try:
                    part = int(part, 10)
                    current = current[part]
                except:
                    raise Config.NotFound(var)
            else:
                raise Config.NotFound(var) 
        return current
    
    def get(self, var, default=None):
        try:
            return self._get(var)
        except Config.NotFound:
            return default

    def set(self, var, value):
        if '.' in var:
            path, _, item = var.rpartition('.')
            current = self._get(path, create=True)
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

    def delete(self, var):
        try:
            if '.' in var:
                path, _, item = var.rpartition('.')
                current = self._get(path)
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
        except (Config.NotFound, KeyError, IndexError):
            pass

    def insert(self, var, value, index=None):
        '''Inserts at the index, and if the index is not provided
        appends to the end of the list
        '''
        current = self._get(var)
        if not isinstance(current, list):
            raise ConfigError('Item is not a list')
        if index is None:
            current.append(value)
        else:
            current.insert(index, value)
        if self.autosave:
            self.save()

    def __repr__(self):
        return 'Config(filename="%(filename)s", format="%(format)s", encoding="%(encoding)s", autosave=%(autosave)s)' % self.__dict__


class MultiConfig(object):
    '''Base class for configuration management'''
    def __init__(self, filename=None, data=None, fmt=None, encoding='utf-8', autosave=True):
        self._configs = []
        self.attach(filename, data, fmt, encoding, autosave)
    
    def attach(self, filename=None, data=None, fmt=None, encoding='utf-8', autosave=True, index=None):
        config = Config(filename, data, fmt, encoding, autosave)
        if index is None:
            self._configs.insert(0, config)
        else:
            self._configs.insert(index, config)
    
    def detach(self, index=None):
        if index is None:
            self._configs.pop(0)
        else:
            self._configs.pop(index)
    
    @property
    def current(self):
        return self._configs[0]
    
    def get(self, var, default=None):
        for config in self._configs:
            try:
                return config._get(var)
            except Config.NotFound:
                pass
        return default
    
    def set(self, var, value):
        self.current.set(var, value)

    def delete(self, var):
        for config in self._configs:
            config.delete(var)

    def insert(self, var, value, index=None):
        self.current.insert(var, value, index)

    def __repr__(self):
        return 'MultiConfig(\n  %s\n)' % (',\n  '.join(map(repr, self._configs)))                    
