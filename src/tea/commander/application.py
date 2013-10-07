__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '18 January 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import os
import sys
import pkgutil
import logging
import collections
from tea import shutil
from tea.utils import six
from tea.utils import get_object
from tea.ds.config import MultiConfig
from tea.commander.base import BaseCommand
from tea.commander.exceptions import CommandError
from tea.commander.ui import ConsoleUserInterface
from tea.commander.commands import AliasCommand, ConfigCommand
from tea.commander.options import create_parser, OPTIONS, DEFAULTS


logger = logging.getLogger(__name__)


class Application(object):
    """Encapsulates the logic of the commander.

    A ManagementUtility has a number of commands, which can be manipulated
    by editing the self.commands dictionary.
    """
    def __init__(self, argv, command_modules, preparser=None,
                 app_config=None, config=None, ui=None):
        """commands: python module path to commands module"""
        self.argv = argv
        self.prog_name = os.path.basename(argv[0])
        if isinstance(command_modules, six.string_types):
            command_modules = [command_modules]
        self._command_modules = command_modules
        self._commands = None
        self._preparser = self._add_options(preparser)
        self._app_config = app_config
        self._config = config or MultiConfig
        self._ui = ui or ConsoleUserInterface()

    def _add_options(self, preparser):
        # Set options
        options = preparser['options']
        group = (None, {'options': []})
        for g in options:
            if g[0] is None:
                group = g
                break
        else:
            options.insert(0, group)
        group[1]['options'].extend(OPTIONS)
        # Set defaults
        defaults = preparser.setdefault('defaults', {})
        defaults.update(DEFAULTS)
        return preparser

    def preparse(self):
        try:
            if self._preparser is None:
                parser = create_parser([])
                check_and_set_func = None
            else:
                parser = create_parser(**{
                    'options': self._preparser.get('options', []),
                    'description': self._preparser.get('description', ''),
                    'defaults': self._preparser.get('defaults', None),
                    'app_config': self._app_config
                })
                check_and_set_func = self._preparser.get('check_and_set_func',
                                                         None)

            (options, args) = parser.parse_known_args(self.argv)
            if check_and_set_func is not None:
                options = check_and_set_func(options)
            # First add options to configuration
            config = self._config(data={'options': options.__dict__})
            # Then add the application specific configuration specified either
            # through the constructor or overridden through the command line
            # options
            app_config = (options.app_config if options.app_config
                          else self._app_config)
            config.ensure_exists(app_config)
            config.attach(filename=app_config)
            return parser, args, config
        except Exception as e:
            logger.exception('')
            raise CommandError('Command arguments error: %s' % e)

    def get_commands(self, config):
        if self._commands is None:
            self._commands = {
                'alias': {
                    'app': 'management',
                    'klass': AliasCommand,
                },
                'config': {
                    'app': 'management',
                    'klass': ConfigCommand,
                },
            }
            # Add additional commands if available
            command_modules = set(self._command_modules[:] +
                                  config.get('options.commands', []) +
                                  config.get('commands', []))
            for module in command_modules:
                package = get_object(module)
                for (loader, module_name, is_pkg) in pkgutil.walk_packages(
                        package.__path__):
                    loader.find_module(module_name).load_module(module_name)
                for command in BaseCommand.__subclasses__():
                    if not command.__module__.startswith('tea.commander'):
                        app, name = command.__module__.split('.')
                        self._commands[name] = {
                            'app': app,
                            'klass': command,
                        }
        return self._commands

    def main_help_text(self, config, commands_only=False):
        """Returns the script's main help text, as a string."""
        if commands_only:
            usage = sorted(self.get_commands(config).keys())
        else:
            usage = [
                '',
                ('Type "%s help <subcommand>" for help on a specific '
                 'subcommand.' % self.prog_name),
                '',
                'Available subcommands:',
            ]
            commands_dict = collections.defaultdict(lambda: [])
            for name, command in self.get_commands(config).items():
                commands_dict[command['app']].append(name)
            for app in sorted(commands_dict.keys()):
                usage.append('')
                usage.append('[%s]' % app)
                for name in sorted(commands_dict[app]):
                    usage.append('    %s' % name)
        return '\n'.join(usage)

    def fetch_command_klass(self, config, subcommand):
        """Tries to fetch the given subcommand, printing a message with the
        appropriate command called from the command line if it can't be found.
        """
        try:
            command = self.get_commands(config)[subcommand]
        except KeyError:
            sys.stderr.write('Unknown command: %r\nType "%s help" for usage.\n'
                             % (subcommand, self.prog_name))
            sys.exit(1)
        return command['klass']

    def execute(self):
        """Given the command-line arguments, this figures out which
        subcommand is being run, creates a parser appropriate to that command,
        and runs it.
        """
        parser, args, config = self.preparse()
        try:
            subcommand = args[1]
        except IndexError:
            subcommand = 'help'  # Display help if no arguments were given.

        # First search in aliases
        if subcommand in config.get('alias', {}):
            alias = shutil.split(config.get('alias.%s' %
                                            subcommand).encode('utf-8'))
            args = [args[0]] + alias + args[2:]
            subcommand = args[1]

        if subcommand == 'help':
            if len(args) <= 2:
                parser.print_help()
                sys.stdout.write(self.main_help_text(config) + '\n')
            elif args[2] == '--commands':
                sys.stdout.write(self.main_help_text(
                    config, commands_only=True) + '\n')
            else:
                self.fetch_command_klass(config, args[2])(config, self._ui)\
                    .print_help(self.prog_name, args[2])
        elif args[1:] in (['--help'], ['-h']):
            parser.print_help()
            sys.stdout.write(self.main_help_text(config) + '\n')
        else:
            self.fetch_command_klass(config, subcommand)(config, self._ui)\
                .run_from_argv(args)
