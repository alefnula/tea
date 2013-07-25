from __future__ import print_function

__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '25 July 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import os
import io
import copy
import logging
from StringIO import StringIO


logger = logging.getLogger(__name__)

class ConfigType:
    DICT = 'dict'
    JSON = 'json' # json files
    YAML = 'yaml' # yaml files
    INI = 'ini'   # ini files
    NA = 'na'     # not available



class ConfigObject(object):
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

    def contains(self, var):
        current = self.data
        for part in var.split('.'):
            if part in current:
                current = current[part]
            else:
                return False
        return True

    def get(self, var, default=None):
        current = self.data
        for part in var.split('.'):
            if part in current:
                current = current[part]
            else:
                return default
        return current

    def set(self, var, value):
        current = self.data
        parts = var.split('.')
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value
        self.__dump()

    def delete(self, var):
        current = self.data
        parts = var.split('.')
        for part in parts[:-1]:
            if part in current:
                current = current[part]
            else:
                return
        del current[parts[-1]]
        self.__dump()

    def add(self, var, value, index=None):
        current = self.data
        parts = var.split('.')
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        last = parts[-1]
        if last in current:
            if not isinstance(current[last], list):
                current[last] = [current[last]]
            if index is not None:
                current[last].insert(int(index), value)
            else:
                current[last].append(value)
        else:
            current[last] = [value]
        self.__dump()

    def remove(self, var, index):
        current = self.__data
        parts = var.split('.')
        for part in parts[:-1]:
            if part in current:
                current = current[part]
            else:
                return
        if isinstance(current[parts[-1]], list):
            try:
                current[parts[-1]].pop(int(index))
            except: pass
        self.__dump()


class Config(object):
    '''Base class for configuration management'''
    def __init__(self, data, fmt=ConfigType.NA, encoding='utf-8'):
        self.__configs = []
        self.attach(data, fmt, encoding)
    
    @property
    def current(self):
        return self.__configs[0]
    
    def attach(self, data, fmt=ConfigType.NA, encoding='utf-8'):
        self.__configs.insert(0, ConfigObject(data, fmt, encoding))
    
    def get(self, var, default=None):
        for config in self.__configs:
            if config.contains(var):
                return config.get(var)
        return default
    
    def set(self, var, value):
        self.current.set(var, value)



if __name__ == '__main__':
    c = Config({'foo': {'bar' : 3}})
    print(c.get('foo'))
    print(c.get('foo.bar'))
