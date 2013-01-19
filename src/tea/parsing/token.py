__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '19 January 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'


class _TokenClass(str):
    def __init__(self, name=None):
        super(_TokenClass, self).__init__(name)
        
    def __getattr__(self, value):
        return _TokenClass(value)

Token = _TokenClass()
