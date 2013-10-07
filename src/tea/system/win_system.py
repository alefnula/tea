__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '02 January 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import os
import win32api  # @UnresolvedImport


get_username = win32api.GetUserName


def get_appdata():
    return os.environ.get('APPDATA', os.path.expanduser('~'))
