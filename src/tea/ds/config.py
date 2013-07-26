from __future__ import print_function

__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '25 July 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import os
import io
import json
import copy
import pickle
import pprint
import logging
try:
    import yaml
    have_yaml = True
except ImportError:
    have_yaml = False


logger = logging.getLogger(__name__)

class ConfigFormat:
    DICT   = 'dict'    # python dictionary
    PICKLE = 'pickle'  # pickle file
    JSON   = 'json'    # json files
    YAML   = 'yaml'    # yaml files
    NA     = 'na'      # not available

    @staticmethod
    def from_filename(filename):
        ext = os.path.splitext(filename)[-1].lower()
        return {
            '.pickle': ConfigFormat.PICKLE,
            '.json': ConfigFormat.JSON,
            '.yaml': ConfigFormat.YAML,
        }.get(ext, ConfigFormat.NA)
    
    @staticmethod
    def load(fmt, data):
        if isinstance(data, dict):
            return ConfigFormat.DICT, copy.deepcopy(data)
        elif fmt == ConfigFormat.JSON:
            try:
                return fmt, json.loads(data)
            except:
                logger.error('Format set to JSON but the data is not valid.')
                return fmt, {}
        elif fmt == ConfigFormat.YAML and have_yaml:
            try:
                return fmt, yaml.safe_load(data)
            except:
                logger.error('Format set to YAML but the data is not valid.')
                return fmt, {}
        elif fmt == ConfigFormat.PICKLE:
            try:
                return fmt, pickle.loads(data)
            except:
                logger.error('Format set to Pickle but the data is not valid.')
        else:
            try:
                return ConfigFormat.JSON, json.loads(data)
            except: pass
            if have_yaml:
                try:
                    return ConfigFormat.YAML, yaml.safe_load(data)
                except: pass
            try:
                return ConfigFormat.PICKLE, pickle.loads(data)
            except: pass
            return ConfigFormat.NA, {}

    @staticmethod
    def dump(filename, fmt, data, encoding):
        if fmt == ConfigFormat.JSON:
            with io.open(filename, 'w+b') as f:
                json.dump(data, f, indent=2, encoding=encoding)
        elif fmt == ConfigFormat.YAML and have_yaml:
            with io.open(filename, 'w', encoding=encoding) as f:
                yaml.safe_dump(data, f, default_flow_style=False)
        elif fmt == ConfigFormat.PICKLE:
            with io.open(filename, 'w', encoding=encoding) as f:
                pickle.dump(data, f)
        

class ConfigError(Exception):
    pass


class Cfg(object):
    class NotFound(Exception):
        pass
    
    def __init__(self, data, fmt=ConfigFormat.NA, encoding='utf-8'):
        self.encoding = encoding
        # Check if the data is a file and if it is read it
        if isinstance(data, basestring) and os.path.isfile(data):
            self.filename = os.path.abspath(data)
            fmt = ConfigFormat.from_filename(self.filename)
            with io.open(self.filename, 'r', encoding=encoding) as f:
                data = f.read()
        else:
            self.filename = None
        if isinstance(data, str):
            data = data.decode(encoding)
        self.fmt, self.data = ConfigFormat.load(fmt, data)

    def __dump(self):
        if self.filename is not None:
            ConfigFormat.dump(self.filename, self.fmt, self.data, self.encoding)

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
        except (Cfg.NotFound, KeyError, IndexError):
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
    def __init__(self, data, fmt=ConfigFormat.NA, encoding='utf-8'):
        self.__cfgs = []
        self.attach(data, fmt, encoding)
    
    @property
    def current(self):
        return self.__cfgs[0]
    
    def attach(self, data, fmt=ConfigFormat.NA, encoding='utf-8'):
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
