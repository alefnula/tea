from __future__ import print_function

__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '07 August 2012'
__copyright__ = 'Copyright (c) 2012 Viktor Kerkez'

from .base import BaseCommand


# Management commands
class AliasCommand(BaseCommand):
    """Alias management

    Usage:
    alias ALIAS        # get alias value
    alias ALIAS VALUE  # set alias value
    """
    id = 'alias'

    def get_alias(self, alias):
        return self.config.get('alias.%s' % alias)

    def set_alias(self, alias, value):
        self.config.set('alias.%s' % alias, value)

    def handle(self, *args, **kwargs):
        l = len(args)
        if l == 0:
            for alias, value in self.config.get('alias', {}).items():
                print('%s="%s"' % (alias, value))
        elif l == 1:
            value = self.get_alias(args[0])
            if value is not None:
                print(value)
        elif l == 2:
            self.set_alias(args[0], args[1])
        else:
            self.print_usage()


class ConfigCommand(BaseCommand):
    """Configuration management

    Usage:
    config list [VAR]             # lists the sub-keys of a var
    config get  VAR               # prints a var
    config set  VAR VALUE         # sets a value to var
    config del  VAR               # deletes a var
    config add  VAR VALUE [INDEX] # add value into list at index
    config rem  VAR INDEX         # removes a value from list by index
    """

    id = 'config'

    def handle(self, *args, **kwargs):
        l = len(args)
        if l < 1:
            self.print_usage()
            return
        command = args[0].lower()
        # List
        if l <= 2 and command == 'list':
            if l == 1:
                for key in self.config.keys():
                    self.ui.message(key)
            else:
                item = self.config.get(args[1])
                if isinstance(item, dict):
                    for key in item:
                        self.ui.message(key)
                elif isinstance(item, list):
                    self.ui.message(', '.join(map(str, range(len(item)))))
        # Get
        elif l == 2 and command == 'get':
            value = self.config.get(args[1])
            if value is not None:
                self.ui.message(value)
        # Set
        elif l == 3 and command == 'set':
            self.config.set(args[1], args[2])
        # Del
        elif l == 2 and command == 'del':
            self.config.delete(args[1])
        # Add
        elif l == 3 and command == 'add':
            item = self.config.get(args[1])
            if item is None:
                self.config.set(args[1], [])
            self.config.insert(args[1], args[2])
        elif l == 4 and command == 'add':
            item = self.config.get(args[1])
            if item is None:
                self.config.set(args[1], [])
            self.config.insert(args[1], args[2], int(args[3]))
        # Rem
        elif l == 3 and command == 'rem':
            self.config.remove(args[1], args[2])
        else:
            self.print_usage()
