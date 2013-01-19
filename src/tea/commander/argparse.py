__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '07 August 2012'
__copyright__ = 'Copyright (c) 2012 Viktor Kerkez'


import os
import json
import string
import logging
import optparse



class LaxOptionParser(optparse.OptionParser):
    '''An option parser that doesn't raise any errors on unknown options.

    This is usefull for preprocessing options before commands.
    '''
    def error(self, msg):
        pass

    def print_help(self):
        '''Output nothing.

        The lax options are included in the normal option parser, so under
        normal usage, we don't need to print the lax options.
        '''
        pass

    def print_lax_help(self):
        '''Output the basic options available to every command.

        This just redirects to the default print_help() behavior.
        '''
        optparse.OptionParser.print_help(self)

    def _process_args(self, largs, rargs, values):
        '''
        Overrides OptionParser._process_args to exclusively handle default
        options and ignore args and other options.

        This overrides the behavior of the super class, which stop parsing
        at the first unrecognized option.
        '''
        while rargs:
            arg = rargs[0]
            try:
                if arg[0:2] == "--" and len(arg) > 2:
                    # process a single long option (possibly with value(s))
                    # the superclass code pops the arg off rargs
                    self._process_long_opt(rargs, values)
                elif arg[:1] == "-" and len(arg) > 1:
                    # process a cluster of short options (possibly with
                    # value(s) for the last one only)
                    # the superclass code pops the arg off rargs
                    self._process_short_opts(rargs, values)
                else:
                    # it's either a non-default option or an arg
                    # either way, add it to the args list so we can keep
                    # dealing with options
                    del rargs[0]
                    raise Exception
            except:
                largs.append(arg)


def add_option(parser, name, conf):
    switches = map(string.strip, name.split(','))
    if 'dest' not in conf:
        conf['dest'] = switches[-1].replace('-', '_')
    if 'default' not in conf:
        conf['default'] = {'store_true': False, 'store_false': True}.get(conf['action'], None)
    swch = []
    for s in switches:
        if len(s) == 1: swch.append('-%s' % s)
        else: swch.append('--%s' % s)
    parser.add_option(*swch, **conf)


def create_parser(options, description='', defaults=None, app_config=None, parser_class=optparse.OptionParser):
    '''Create a options parser form configuration
    
    options:           dictionary of configurations
    defaults:          default values
    configuration:     name of the plist file with default options for this user
    ''' 
    parser = parser_class()
    parser.description = description
    
    # Load Options
    for group_name, data in options:
        if group_name is None:
            group = parser
        else:
            group = optparse.OptionGroup(parser, group_name, data['help'] if 'help' in data else '')        
        for name, conf in data['options']:
            add_option(group, name, conf)
        if group_name is not None:
            parser.add_option_group(group)
    
    # Set Defaults
    if defaults is not None:
        for key, value in defaults.items():
            parser.set_defaults(**{key.replace('-', '_'): value})
    
    # Set User Defaults
    if app_config is not None:
        if os.path.isfile(app_config):
            try:
                with open(app_config, 'rb') as app_config_file:
                    data = json.load(app_config_file)
                    for key, value in data.get('options', {}).items():
                        parser.set_defaults(**{key.replace('-', '_'): value})
            except:
                logging.error('Error while parsing: %s' % app_config)
    return parser


def parse_arguments(args, options, description='', defaults=None, app_config=None, check_and_set_func=None, parser_class=optparse.OptionParser):
    '''Create a options parser form configuration and parse arguments
    
    args:               arguments to parse
    options:            dictionary of configurations
    defaults:           default values
    inifile:            ini file with default values for this user
    check_and_set_func: function that receives options, and checks and sets additional values
    ''' 
    parser = create_parser(options, description, defaults, app_config, parser_class)
    if args is None: args = []
    (options, args) = parser.parse_args(args)
    if check_and_set_func is not None:
        options = check_and_set_func(options)    
    return options
