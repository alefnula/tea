from __future__ import print_function

__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '18 January 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import sys

b = lambda x: x.lower() in ('true', 't')

commands = {
    # Function name : (Iterable result, [Param types], Number of required arguments)])
    'search' : (True,  [str, str, b, b], 2),
    'chdir'  : (False, [str],            1),
    'mkdir'  : (False, [str],            1),
    'copy'   : (False, [str, str],       2),
    'gcopy'  : (False, [str, str],       2),
    'move'   : (False, [str, str],       2),
    'gmove'  : (False, [str, str],       2),
    'remove' : (False, [str],            1),
}


def print_help():
    print('Usage: python -m tea.shutil [command] [params]\nCommands: %s' %
          ', '.join(commands.keys()))
    return 1


def print_func_help(func, required):
    import inspect
    args = inspect.getargspec(func).args
    print('Usage: %s' % func.__name__, end=' ')
    for i in range(required):
        print(args[i], end=' ')
    if required < len(args):
        print('[%s]' % ' '.join(args[required:]))
    return 1


def main(args):
    # Configure logger
    import logging
    from tea.logger import configure_logging
    configure_logging(stdout_level=logging.WARNING)

    if len(args) == 0:
        print_help()
    else:
        command = args[0]
        if command == 'help' or command not in commands:
            return print_help()
        else:
            args = args[1:]
            # get specs
            iterable, params, required = commands[command]
            # import function
            from tea import shutil
            func = getattr(shutil, command)
            if not (required <= len(args) <= len(params)):
                return print_func_help(func, required)
            parsed_args = []
            for i, arg in enumerate(args):
                try:
                    parsed_args.append(params[i](arg))
                except:
                    print('Failed to parse argument: %s' % arg)
                    return 1
            try:
                if iterable:
                    for i in func(*parsed_args):
                        print(i)
                else:
                    if func(*parsed_args):
                        print('OK')
                        return 0
                    else:
                        print('FAILED')
                        return 1
            except Exception as e:
                print('ERROR: %s' % e)
                return 1
            return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
