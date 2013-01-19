__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '07 August 2012'
__copyright__ = 'Copyright (c) 2012 Viktor Kerkez'

import os
import json
import logging

# tea imports
from tea import shutil



class BaseConfig(object):
    '''Base class for application configuration'''
    def __init__(self, options, app_config=None):
        self.__options       = options
        self.__app_config    = app_config
        self.__configuration = None

    @property
    def configuration(self):
        if self.__configuration is None:
            if os.path.isfile(self.__app_config):
                try:
                    with open(self.__app_config, 'rb') as app_config_file:
                        self.__configuration = json.load(app_config_file, encoding='utf-8')
                except:
                    logging.exception('Error reading: %s' % self.__app_config)
                    self.__configuration = {}
            else:
                self.__configuration = {}
        return self.__configuration

    def __write_config(self):
        if not os.path.isdir(os.path.dirname(self.__app_config)):
            shutil.mkdir(os.path.dirname(self.__app_config))
        with open(self.__app_config, 'wb') as app_config_file:
            json.dump(self.configuration, app_config_file, indent=4, encoding='utf-8')

    def get(self, var, default=None):
        if var.startswith('options.'):
            key = var.replace('options.', '').replace('-', '_')
            try: return getattr(self.__options, key)
            except: return default
        current = self.configuration
        for part in var.split('.'):
            if part in current:
                current = current[part]
            else:
                return default
        return current

    def set(self, var, value):
        current = self.configuration
        parts = var.split('.')
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value
        self.__write_config()
    
    def delete(self, var):
        current = self.configuration
        parts = var.split('.')
        for part in parts[:-1]:
            if part in current:
                current = current[part]
            else:
                return
        del current[parts[-1]]
        self.__write_config()

    def add(self, var, value, index=None):
        current = self.configuration
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
        self.__write_config()

    def remove(self, var, index):
        current = self.configuration
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
        self.__write_config()

    def __getattr__(self, attr):
        if hasattr(self.__options, attr):
            return getattr(self.__options, attr)
        raise AttributeError(attr)
