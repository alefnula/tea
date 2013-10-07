__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '07 August 2012'
__copyright__ = 'Copyright (c) 2012 Viktor Kerkez'

import logging
import argparse

logger = logging.getLogger(__name__)


OPTIONS = [
    ('q, quiet', {
        'action': 'store_const',
        'dest': 'report_format',
        'const': 'quiet',
        'default': None,
        'help': 'Do not print anything to stdout.  [ False ]',
    }),
    ('logfile', {
        'action': 'store',
        'type': str,
        'help': 'Log file.                         [ %(default)s ]',
    }),
    ('app-config', {
        'action': 'store',
        'type': str,
        'metavar': 'CONFIG',
        'help': '''Path to a configuration file for the application. This
                    option will override the default value provided by the
                    application and use this one instead. [ %(default)s ]''',
    }),
    ('commands', {
        'dest': 'commands',
        'action': 'append',
        'type': str,
        'help': '''Paths to additional modules from which commands should
                    be loaded. Paths should represent valid python paths ands
                    modules should be in python path.      [ none ]''',
    }),
    ('report-json', {
        'action': 'store_const',
        'dest': 'report_format',
        'const': 'json',
        'default': None,
        'help': 'Print out report in json format.  [ False ]',
    }),
]

DEFAULTS = {
    'logfile': 'sv.log',
    'commands': [],
}


def add_option(parser, name, conf):
    # HACK: For positional arguments there are no switches
    switches = ([sw.strip() for sw in name.split(',')]
                if name is not None else [])
    # Default dest is long_switch.replace('-', '_')
    if 'dest' not in conf:
        conf['dest'] = switches[-1].replace('-', '_')
    # Default default is None or opposite of store_true/store_false
    if 'default' not in conf:
        conf['default'] = {'store_true': False,
                           'store_false': True}.get(conf['action'], None)
    # Default type for store is str
    if 'type' not in conf and conf['action'] == 'store':
        conf['type'] = str
    swch = []
    for s in switches:
        if len(s) == 1:
            swch.append('-%s' % s)
        else:
            swch.append('--%s' % s)
    parser.add_argument(*swch, **conf)


def create_parser(options, description='', defaults=None, app_config=None):
    """Create a options parser form configuration

    :param options: dictionary of configurations
    :param defaults: default values
    :param configuration: name of the json file with default options for this
        user
    """
    parser = argparse.ArgumentParser()
    parser.description = description
    # Load Options
    for group_name, data in options:
        if group_name is None:
            group = parser
        else:
            group = parser.add_argument_group(group_name,
                                              data['help'] if 'help' in data
                                              else '')
        for name, conf in data['options']:
            add_option(group, name, conf)
    # Set Defaults
    if defaults is not None:
        for key, value in defaults.items():
            parser.set_defaults(**{key.replace('-', '_'): value})
    return parser


def parse_arguments(args, options, description='', defaults=None,
                    app_config=None, check_and_set_func=None):
    """Create a options parser form configuration and parse arguments

    :param args:     arguments to parse
    :param options:  dictionary of configurations
    :param defaults: default values
    :param inifile:  ini file with default values for this user
    :param check_and_set_func: function that receives options, and checks and
        sets additional values
    """
    parser = create_parser(options, description, defaults, app_config)
    if args is None:
        args = []
    (options, args) = parser.parse_args(args)
    if check_and_set_func is not None:
        options = check_and_set_func(options)
    return options
