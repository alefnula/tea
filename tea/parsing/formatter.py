__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '19 January 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import sys
from tea.utils import six
from tea.console.color import cprint
from tea.parsing.token import Token
from tea.parsing.style import Style, ConsoleStyleAdapter


class Formatter(object):
    """Formatter class

    Properties:

    lexer:  Current lexer
    style:  Current style
    stream: Current output stream (if not set use sys.stdout)
    """

    def __init__(self, lexer=None, style=None, stream=None):
        self._lexer = lexer
        self._style = style
        self._stream = stream or sys.stdout

    def get_lexer(self):
        return self._lexer

    def set_lexer(self, value):
        self._lexer = value

    def get_style(self):
        if self._style is None:
            self._style = Style()
        return self._style

    def set_style(self, value):
        self._style = value

    def get_stream(self):
        return self._stream

    def set_stream(self, value):
        self._stream = value

    # Properties
    lexer = property(get_lexer,  set_lexer)
    style = property(get_style,  set_style)
    stream = property(get_stream, set_stream)

    def format(self, data):
        """Use this method for formatting data"""
        if self.lexer is None:
            self.format_text(self.style.get(Token.Text), six.text_type(data))
        else:
            for token, text in self.lexer.tokenize(data):
                self.format_text(self.style.get(token), text)

    def format_text(self, style, text):
        """Format a single peace of a text using the provided style"""
        raise NotImplementedError()


class ConsoleFormatter(Formatter):
    """Simple console output formatter using ConsoleStyleAdapter
    and tea.console.color cprint
    """

    def get_style(self):
        if self._style is None:
            self._style = ConsoleStyleAdapter(Style)
        return self._style

    def set_style(self, value):
        self._style = ConsoleStyleAdapter(value)

    # Properties
    style = property(get_style, set_style)

    def format_text(self, style, text):
        fg, fg_dark = style['fg']
        bg, bg_dark = style['bg']
        cprint(text, fg=fg, bg=bg, fg_dark=fg_dark, bg_dark=bg_dark)
