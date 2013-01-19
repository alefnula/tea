__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '19 January 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

class Formatter(object):
    def __init__(self, lexer, style, stream):
        self.lexer  = lexer
        self.style  = style
        self.stream = stream
    
    def format(self, text):
        for token, text in self.lexer.get_tokens(text):
            self.format_token(token, text)
    
    def format_token(self, token, text):
        raise NotImplementedError()
