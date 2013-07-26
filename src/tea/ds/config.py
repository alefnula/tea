from __future__ import print_function

__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '25 July 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import os
import io
import copy
import pprint
import logging
from StringIO import StringIO


logger = logging.getLogger(__name__)

class ConfigType:
    DICT = 'dict'
    JSON = 'json' # json files
    YAML = 'yaml' # yaml files
    INI = 'ini'   # ini files
    NA = 'na'     # not available


class ConfigError(Exception):
    pass


class Cfg(object):
    class NotFound(Exception):
        pass
    
    def __init__(self, data, fmt=ConfigType.NA, encoding='utf-8'):
        if isinstance(data, (dict, list, tuple)):
            self.filename = None
            self.fmt = ConfigType.DICT
            self.encofing = encoding
            self.data = copy.deepcopy(data)
        elif isinstance(data, basestring):
            if os.path.isfile(data):
                self.filename = os.path.abspath(data)
                self.fmt = self.__get_fmt(fmt, filename=self.filename)
                self.encoding = encoding
                self.data = self.__load()
            else:
                self.filename = None
                self.encoding = encoding
                if isinstance(data, str):
                    data = str.decode(encoding)
                self.fmt = self.__get_fmt(fmt, data=data)
                self.data = self.__load(data)
        else:
            self.filename = None
            self.fmt = fmt
            self.encofing = encoding
            self.data = {}
                
    def __get_fmt(self, fmt, filename=None, data=None):
        # First check if type is provided and if it's valid
        if fmt in (ConfigType.JSON, ConfigType.YAML, ConfigType.INI):
            return fmt
        if filename is not None:
            ext = os.path.splitext(data)[-1].lower()
            return {
                '.json': ConfigType.JSON,
                '.yaml': ConfigType.YAML,
                '.ini': ConfigType.INI, 
            }.get(ext, ConfigType.NA)
        if data is not None:
            try:
                import json
                json.loads(data)
                return ConfigType.JSON
            except: pass
            try:
                import yaml
                yaml.safe_load(data)
                return ConfigType.YAML
            except: pass
            try:
                from ConfigParser import ConfigParser
                ConfigParser.readfp(StringIO(data))
                return ConfigType.INI
            except: pass
        return ConfigType.NA

    def __load(self, data=None):
        if self.fmt == ConfigType.JSON:
            import json
            if data is not None:
                return json.loads(data)
            else:
                with io.open(self.filename, 'r', encoding=self.encoding) as f:
                    return json.load(f)
        elif self.fmt == ConfigType.YAML:
            import yaml
            if data is not None:
                return yaml.safe_load(data)
            else:
                with io.open(self.filename, 'r', encoding=self.encoding) as f:
                    return yaml.safe_load(f)
        return {}

    def __dump(self):
        if self.filename is not None:
            if self.fmt == ConfigType.JSON:
                import json
                with io.open(self.filename, 'w', encoding=self.encoding) as f:
                    json.dump(self.data, f)
            elif self.fmt == ConfigType.YAML:
                import yaml
                with io.open(self.filename, 'w', encoding=self.encofing) as f:
                    yaml.safe_dump(self.data, f)

    def _get(self, var, create=False):
        current = self.data
        for part in var.split('.'):
            if isinstance(current, dict):
                if part in current:
                    current = current[part]
                elif create:
                    current = current.setdefault(part, {})
                else:
                    raise Cfg.NotFound(var)
            elif isinstance(current, list):
                try:
                    part = int(part, 10)
                    current = current[part]
                except:
                    raise Cfg.NotFound(var)
            else:
                raise Cfg.NotFound(var) 
        return current
    
    def get(self, var):
        return self._get(var)

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
        self.__dump()

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
            self.__dump()
        except Cfg.NotFound:
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
        self.__dump()

    def __repr__(self):
        return 'Cfg(%s)' % pprint.saferepr(self.data)


class Config(object):
    '''Base class for configuration management'''
    def __init__(self, data, fmt=ConfigType.NA, encoding='utf-8'):
        self.__cfgs = []
        self.attach(data, fmt, encoding)
    
    @property
    def current(self):
        return self.__cfgs[0]
    
    def attach(self, data, fmt=ConfigType.NA, encoding='utf-8'):
        self.__cfgs.insert(0, Cfg(data, fmt, encoding))
    
    def get(self, var, default=None):
        for cfg in self.__cfgs:
            try:
                return cfg.get(var)
            except Cfg.NotFound:
                pass
        return default
    
    def set(self, var, value):
        self.current.set(var, value)

    def delete(self, var):
        for cfg in self.__cfgs:
            cfg.delete(var)

    def insert(self, var, value, index=None):
        self.current.insert(var, value, index)

    def __repr__(self):
        def merge(d1, d2):
            for key in d2:
                if key not in d1:
                    d1[key] = copy.deepcopy(d2[key])
                elif isinstance(d2[key], dict):
                    merge(d1[key], d2[key])
                else:
                    d1[key] = copy.deepcopy(d2[key])
        d = {}
        for cfg in reversed(self.__cfgs):
            merge(d, cfg.data)
        return 'Config(%s)' % pprint.saferepr(d)
                    

if __name__ == '__main__':
    c = Config({'foo': {'bar' : 3}})
    print(c.get('foo'))
    print(c.get('foo.bar'))
