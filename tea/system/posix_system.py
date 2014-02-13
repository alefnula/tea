__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '02 January 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import os
import getpass


get_username = getpass.getuser


def get_appdata():
    return os.path.join(os.path.expanduser('~'), '.config')
