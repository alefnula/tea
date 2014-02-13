__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '18 January 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import os
import re
import sys
import json
import time
import logging
import argparse
from tea.commander.options import add_option
from tea.commander.exceptions import CommandError

logger = logging.getLogger(__name__)


LEADING_WHITESPACE_REMOVER_RE = re.compile('^    ', re.MULTILINE)


class BaseCommand(object):
    """The base class from which all management commands ultimately derive.

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
    """
    # Metadata about this command.
    option_list = tuple()
    args = ''

    def __init__(self, config, ui):
        self.id = str(self).split('.')[-1]
        self.config = config
        self.ui = ui

    def __str__(self):
        return self.__class__.__module__

    def usage(self, subcommand=None):
        """Return a brief description of how to use this command, by
        default from the attribute ``self.__doc__``.
        """
        if subcommand is None:
            subcommand = self.id
        usage = '%s [options] %s' % (subcommand, self.args)
        if self.__doc__:
            return '%s\n\n%s' % (
                usage, LEADING_WHITESPACE_REMOVER_RE.sub('', self.__doc__))
        else:
            return usage

    def print_usage(self):
        self.ui.info(self.usage())

    def create_parser(self, prog_name, subcommand):
        """Create and return the ``OptionParser`` which will be used to
        parse the arguments to this command.
        """
        parser = argparse.ArgumentParser(prog=os.path.basename(prog_name),
                                         usage=self.usage(subcommand))
        for name, conf in self.option_list:
            add_option(parser, name, conf)
        return parser

    def print_help(self, prog_name, subcommand):
        """Print the help message for this command, derived from
        ``self.usage()``.
        """
        parser = self.create_parser(prog_name, subcommand)
        parser.print_help()

    def run_from_argv(self, argv):
        """Set up any environment changes requested (e.g., Python path,
        then run this command.
        """
        parser = self.create_parser(argv[0], argv[1])
        options, args = parser.parse_known_args(argv[2:])
        self.execute(*args, **options.__dict__)

    def execute(self, *args, **options):
        """Try to execute this command, performing validations if
        needed (as controlled by the attributes. If the command
        raises a ``CommandError``, intercept it and print it sensibly
        to stderr.
        """
        try:
            # FIXME: Why do I need this?!
            self.stdout = options.get('stdout', sys.stdout)
            self.stderr = options.get('stderr', sys.stderr)
            self.validate()

            # Setup lexer and style
            lexer = self.ui.formatter.lexer
            style = self.ui.formatter.style
            if hasattr(self, 'Lexer'):
                self.ui.formatter.lexer = self.Lexer()
            if hasattr(self, 'Style'):
                self.ui.formatter.style = self.Style
            if hasattr(self, 'LexerConfig'):
                self.ui.formatter.lexer.push_config(self.LexerConfig)

            self._start_time = time.time()  # Start report timer
            output = self.handle(*args, **options)

            # Teardown lexer and style
            if hasattr(self, 'LexerConfig'):
                self.ui.formatter.lexer.pop_config()
            if hasattr(self, 'Style'):
                self.ui.formatter.style = style
            if hasattr(self, 'Lexer'):
                self.ui.formatter.lexer = lexer

            if self.config.get('options.report_format') == 'json':
                self.stdout.write(json.dumps(self._report, indent=4))
            if output:
                self.stdout.write(output)
        except CommandError as e:
            logger.exception('Command %s failed' % self)
            self.stderr.write('Error: %s\n' % e)
            sys.exit(1)

    def validate(self):
        """Validates the given command, raising CommandError for any errors."""
        pass

    def handle(self, *args, **options):
        """The actual logic of the command. Subclasses must implement this
        method.
        """
        raise NotImplementedError()


class LabelCommand(BaseCommand):
    """A management command which takes one or more arbitrary arguments
    (labels) on the command line, and does something with each of
    them.

    Rather than implementing ``handle()``, subclasses must implement
    ``handle_label()``, which will be called once for each label.
    """
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
        """Perform the command's actions for ``label``, which will be the
        string as given on the command line.
        """
        raise NotImplementedError()


class NoArgsCommand(BaseCommand):
    """A command which takes no arguments on the command line.

    Rather than implementing ``handle()``, subclasses must implement
    ``handle_noargs()``; ``handle()`` itself is overridden to ensure
    no arguments are passed to the command.

    Attempting to pass arguments will raise ``CommandError``.
    """
    args = ''

    def handle(self, *args, **options):
        if args:
            raise CommandError("Command doesn't accept any arguments")
        return self.handle_noargs(**options)

    def handle_noargs(self, **options):
        """Perform this command's actions."""
        raise NotImplementedError()
