__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '07 August 2012'
__copyright__ = 'Copyright (c) 2012 Viktor Kerkez'

'''Base classes for writing management commands.'''

import os
import re
import sys
import json
import time
import shlex
import collections
from optparse import OptionParser

# tea imports
from tea import shutil
from tea.utils import get_object
from tea.logger import * #@UnusedWildImport
from tea.console.color import cprint, Color
from tea.commander.argparse import create_parser, LaxOptionParser

from .config import BaseConfig


LEADING_WHITESPACE_REMOVER_RE = re.compile('^    ', re.MULTILINE)


class CommandError(Exception):
    '''
    Exception class indicating a problem while executing a command.

    If this exception is raised during the execution of a management
    command, it will be caught and turned into a nicely-printed error
    message to the appropriate output stream (i.e., stderr); as a
    result, raising this exception (with a sensible description of the
    error) is the preferred way to indicate that something has gone
    wrong in the execution of a command.
    '''
    pass




class BaseCommand(object):
    '''
    The base class from which all management commands ultimately derive.

    Use this class if you want access to all of the mechanisms which
    parse the command-line arguments and work out what code to call in
    response; if you don't need to change any of that behavior,
    consider using one of the subclasses defined in this file.

    If you are interested in overriding/customizing various aspects of
    the command-parsing and -execution behavior, the normal flow works
    as follows:

    1. Loads the command class and calls its ``run_from_argv()`` method.

    2. The ``run_from_argv()`` method calls ``create_parser()`` to get
       an ``OptionParser`` for the arguments, parses them, performs
       any environment changes requested by options, and then calls the
       ``execute()`` method, passing the parsed arguments.

    3. The ``execute()`` method attempts to carry out the command by
       calling the ``handle()`` method with the parsed arguments; any
       output produced by ``handle()`` will be printed to standard
       output.

    4. If ``handle()`` raised a ``CommandError``, ``execute()`` will
       instead print an error message to ``stderr``.

    Thus, the ``handle()`` method is typically the starting point for
    subclasses.

    Several attributes affect behavior at various steps along the way:

    ``args``
        A string listing the arguments accepted by the command,
        suitable for use in help messages; e.g., a command which takes
        a list of application names might set this to '<appname
        appname ...>'.

     ``option_list``
        This is the list of ``optparse`` options which will be fed
        into the command's ``OptionParser`` for parsing arguments.
    '''
    # Metadata about this command.
    option_list = tuple()
    args        = ''
    
    # Statuses is a mapping between a result status and its
    # representation. Report will search for a perticular status
    # number, and if it doesnt find it, it will use the None, as
    # default. The tuple is in a format:
    # (short message, successfull status, console color) 
    statuses = {
          0 : ('ok',     True,  Color.green),
       None : ('failed', False, Color.red),
    }
    
    def __init__(self, config):
        self.id       = str(self).split('.')[-1]
        self.config   = config
        # Reporting
        self._start_time = None
        self._report     = {
            'id'         : self.id,
            'operations' : [], 
        }

    def add_result(self, target, status=0, output='', error=''):
        if not isinstance(target, dict):
            if hasattr(target, '__serialize__'):
                target = target.__serialize__()
            else:
                target = {'name' : str(target)}
        status_data = self.statuses.get(status, self.statuses.get(None))
        operation = {
            'target'     : target,
            'start_time' : self._start_time,
            'end_time'   : time.time(),
            'status'     : status,
            'output'     : output,
            'error'      : error,
            'message'    : status_data[0],
            'succeeded'  : status_data[1],
            'color'      : status_data[2],
        }
        self._report['operations'].append(operation)
        if self.config.report_format is None:
            self.present(operation)
        self._start_time = time.time()

    def __str__(self):
        return self.__class__.__module__

    def usage(self, subcommand=None):
        '''Return a brief description of how to use this command, by
        default from the attribute ``self.__doc__``.
        '''
        if subcommand is None: subcommand = self.id
        usage = '%%prog %s [options] %s' % (subcommand, self.args)
        if self.__doc__:
            return '%s\n\n%s' % (usage, LEADING_WHITESPACE_REMOVER_RE.sub('', self.__doc__))
        else:
            return usage

    def create_parser(self, prog_name, subcommand):
        '''Create and return the ``OptionParser`` which will be used to
        parse the arguments to this command.
        '''
        return OptionParser(prog=os.path.basename(prog_name), usage=self.usage(subcommand), option_list=self.option_list)

    def print_help(self, prog_name, subcommand):
        '''Print the help message for this command, derived from ``self.usage()``. '''
        parser = self.create_parser(prog_name, subcommand)
        parser.print_help()

    def run_from_argv(self, argv):
        '''Set up any environment changes requested (e.g., Python path,
        then run this command.
        '''
        parser = self.create_parser(argv[0], argv[1])
        options, args = parser.parse_args(argv[2:])
        self.execute(*args, **options.__dict__)

    def execute(self, *args, **options):
        '''Try to execute this command, performing validations if
        needed (as controlled by the attributes. If the command
        raises a ``CommandError``, intercept it and print it sensibly
        to stderr.
        '''
        try:
            # FIXME: Why do I need this?!
            self.stdout = options.get('stdout', sys.stdout)
            self.stderr = options.get('stderr', sys.stderr)
            self.validate()
            self._start_time = time.time() # Start report timer
            output = self.handle(*args, **options)
            if self.config.report_format == 'json':
                self.stdout.write(json.dumps(self._report, indent=4))
            if output:
                self.stdout.write(output)
        except CommandError, e:
            LOG_EXCEPTION('Command %s failed' % self)
            self.stderr.write('Error: %s\n' % e)
            sys.exit(1)

    def validate(self):
        '''Validates the given command, raising CommandError for any errors.'''
        pass

    def handle(self, *args, **options):
        '''The actual logic of the command. Subclasses must implement this method.'''
        raise NotImplementedError()
    
    def present(self, operation):
        '''This is a method for presenting an operation to user
        
        Default implementation just prints out the target name in
        operation default color and user can override this method
        ''' 
        cprint('%s\n' % operation['target']['name'], operation['color'])



class LabelCommand(BaseCommand):
    '''A management command which takes one or more arbitrary arguments
    (labels) on the command line, and does something with each of
    them.

    Rather than implementing ``handle()``, subclasses must implement
    ``handle_label()``, which will be called once for each label.
    '''
    args = '<label label ...>'
    label = 'label'

    def handle(self, *labels, **options):
        if not labels:
            raise CommandError('Enter at least one %s.' % self.label)

        output = []
        for label in labels:
            label_output = self.handle_label(label, **options)
            if label_output:
                output.append(label_output)
        return '\n'.join(output)

    def handle_label(self, label, **options):
        '''Perform the command's actions for ``label``, which will be the
        string as given on the command line.
        '''
        raise NotImplementedError()



class NoArgsCommand(BaseCommand):
    '''
    A command which takes no arguments on the command line.

    Rather than implementing ``handle()``, subclasses must implement
    ``handle_noargs()``; ``handle()`` itself is overridden to ensure
    no arguments are passed to the command.

    Attempting to pass arguments will raise ``CommandError``.
    '''
    args = ''

    def handle(self, *args, **options):
        if args:
            raise CommandError("Command doesn't accept any arguments")
        return self.handle_noargs(**options)

    def handle_noargs(self, **options):
        '''Perform this command's actions.'''
        raise NotImplementedError()


# Management commands
class AliasCommand(BaseCommand):
    '''Alias management
    
    Usage:
    alias ALIAS        # get alias value
    alias ALIAS VALUE  # set alias value
    '''
    id = 'alias'

    def get_alias(self, alias):
        return self.config.get('alias.%s' % alias)

    def set_alias(self, alias, value):
        self.config.set('alias.%s' % alias, value)

    def handle(self, *args, **kwargs):
        l = len(args)
        if l == 0:
            for alias, value in self.config.get('alias', {}).items():
                print '%s="%s"' % (alias, value)
        elif l == 1:
            value = self.get_alias(args[0])
            if value is not None:
                print value
        elif l == 2:
            self.set_alias(args[0], args[1])
        else:
            print self.usage()


class ConfigCommand(BaseCommand):
    '''Configuration management

    Usage:
    config get VAR               # prints a var
    config set VAR VALUE         # sets a value to var
    config del VAR               # deletes a var
    config add VAR VALUE [INDEX] # add value into list assosiated with the var (at index)
    config rem VAR INDEX         # removes a value from list by index
    '''
    
    id = 'config'

    def handle(self, *args, **kwargs):
        l = len(args)
        if l < 2:
            print self.usage()
            return
        command = args[0].lower()
        # Get
        if l == 2 and command == 'get': 
            value = self.config.get(args[1])
            if value is not None:
                print value
        # Set
        elif l == 3 and command == 'set':
            self.config.set(args[1], args[2])
        # Del
        elif l == 2 and command == 'del':
            self.config.delete(args[1])
        # Add
        elif l == 3 and command == 'add':
            self.config.add(args[1], args[2])
        elif l == 4 and command == 'add':
            self.config.add(args[1], args[2], args[3])
        # Rem
        elif l == 3 and command == 'rem':
            self.config.remove(args[1], args[2])
        else:
            print self.usage()


class ManagementUtility(object):
    '''Encapsulates the logic of the at.py utility.

    A ManagementUtility has a number of commands, which can be manipulated
    by editing the self.commands dictionary.
    '''
    def __init__(self, argv, commands, preparser=None, app_config=None, config=None):
        '''commands: python module path to commands module'''
        self.argv = argv
        self.prog_name = os.path.basename(argv[0])
        self._commands_path = commands
        self._commands = None
        self._preparser = self._add_options(preparser)
        self._app_config = app_config
        self._config = config or BaseConfig

    def _add_options(self, preparser):
        options = preparser['options']
        group = (None, {'options': []})
        for g in options:
            if g[0] is None:
                group = g
                break
        else:
            options.insert(0, group)
        group[1]['options'].extend([
            ('q, quiet', {
                'action'  : 'store_const',
                'dest'    : 'report_format',
                'const'   : 'quiet',
                'default' : None,
                'help'    : 'Do not print anything to stdout.  [ False ]',
            }),
            ('report-json', {
                'action'  : 'store_const',
                'dest'    : 'report_format',
                'const'   : 'json',
                'default' : None,
                'help'    : 'Print out report in json format.  [ False ]',
            }),
            ('report-plist', {
                'action'  : 'store_const',
                'dest'    : 'report_format',
                'const'   : 'plist',
                'default' : None,
                'help'    : 'Print out report in plist format. [ False ]',
            }),
        ])
        return preparser

    def preparse(self):
        try:
            if self._preparser is None:
                parser = create_parser([], parser_class=LaxOptionParser)
                check_and_set_func = None
            else:
                parser = create_parser(**{
                    'options'      : self._preparser.get('options',     []),
                    'description'  : self._preparser.get('description', ''),
                    'defaults'     : self._preparser.get('defaults',    None),
                    'app_config'   : self._app_config,
                    'parser_class' : LaxOptionParser
                })
                check_and_set_func = self._preparser.get('check_and_set_func', None)
                
            (options, args) = parser.parse_args(self.argv)
            if check_and_set_func is not None:
                options = check_and_set_func(options)
            config = self._config(options, self._app_config)
            return parser, args, config
        except Exception, e:
            raise CommandError('Command arguments error: %s' % e)

    def get_commands(self):
        if self._commands is None:
            self._commands = {
                'alias' : {
                    'app'   : 'management',
                    'klass' : AliasCommand,
                },
                'config' : {
                    'app'   : 'management',
                    'klass' : ConfigCommand,
                },
            }
            commands = get_object(self._commands_path) 
            commands_dir = os.path.dirname(commands.__file__)
            for filename in (f for f in shutil.search(commands_dir, '*.py') if not os.path.basename(f).startswith('__')):
                LOG_DEBUG('Loading filename: %s' % filename)
                try:
                    app, name = os.path.splitext(filename)[0].replace(commands_dir, '').strip(os.sep).split(os.sep)
                    self._commands[name] = {
                        'app'   : app,
                        'klass' : get_object('%s.%s.Command' % (app, name), commands),
                    }
                    LOG_DEBUG('Loading filename succeeded: %s' % filename)
                except:
                    LOG_ERROR('Loading filename failed: %s' % filename)
        return self._commands

    def main_help_text(self, commands_only=False):
        '''Returns the script's main help text, as a string.'''
        if commands_only:
            usage = sorted(self.get_commands().keys())
        else:
            usage = [
                '',
                'Type "%s help <subcommand>" for help on a specific subcommand.' % self.prog_name,
                '',
                'Available subcommands:',
            ]
            commands_dict = collections.defaultdict(lambda: [])
            for name, command in self.get_commands().iteritems():
                commands_dict[command['app']].append(name)
            for app in sorted(commands_dict.keys()):
                usage.append('')
                usage.append('[%s]' % app)
                for name in sorted(commands_dict[app]):
                    usage.append('    %s' % name)
        return '\n'.join(usage)

    def fetch_command_klass(self, subcommand):
        '''Tries to fetch the given subcommand, printing a message with the
        appropriate command called from the command line if it can't be found.
        '''
        try:
            command = self.get_commands()[subcommand]
        except KeyError:
            sys.stderr.write("Unknown command: %r\nType '%s help' for usage.\n" % \
                (subcommand, self.prog_name))
            sys.exit(1)
        return command['klass']

    def execute(self):
        '''Given the command-line arguments, this figures out which subcommand is
        being run, creates a parser appropriate to that command, and runs it.
        '''
        parser, args, config = self.preparse()
        try:
            subcommand = args[1]
        except IndexError:
            subcommand = 'help' # Display help if no arguments were given.
            
        # First search in aliases
        if subcommand in config.get('alias', {}):
            args = [args[0]] + shlex.split(config.get('alias.%s' % subcommand)) + args[2:]
            subcommand = args[1]
        
        if subcommand == 'help':
            if len(args) <= 2:
                parser.print_lax_help()
                sys.stdout.write(self.main_help_text() + '\n')
            elif args[2] == '--commands':
                sys.stdout.write(self.main_help_text(commands_only=True) + '\n')
            else:
                self.fetch_command_klass(args[2])(config).print_help(self.prog_name, args[2])
        elif args[1:] in (['--help'], ['-h']):
            parser.print_lax_help()
            sys.stdout.write(self.main_help_text() + '\n')
        else:
            self.fetch_command_klass(subcommand)(config).run_from_argv(args)



def execute_from_command_line(argv, commands, preparser=None, app_config=None, config=None):
    '''A simple method that runs a ManagementUtility.'''
    utility = ManagementUtility(argv, commands, preparser, app_config, config)
    utility.execute()
