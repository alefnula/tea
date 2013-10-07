__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '19 January 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import re
import abc
from tea.utils import six
from tea.parsing.token import Token


class Lexer(six.with_metaclass(abc.ABCMeta)):
    config = None

    def __init__(self):
        self._config_stack = []

    def push_config(self, config):
        self._config_stack.append(self.config)
        self.config = config

    def pop_config(self):
        config = self.config
        self.config = self._config_stack.pop()
        return config

    def preprocess(self, data):
        return data

    def tokenize(self, data):
        """This methods receives an arbitrary data and returns an iterable
        of (token, text) pairs generated from data.

        For example it can receive text:

        >>> lexer = MyTextLexer()
        >>> text = 'Name: John Doe\nAge: 33'
        >>> for token, text in lexer.tokenize(text):
                print '%-7s %s' % (token, repr(text))

        Header  'Name: '
        Text    'John Doe'
        Header  'Age: '
        Text    '33'
        >>>

        Or it can receive an arbitrary data

        >>> lexer = MyStatusLexer()
        >>> data = [{'status': 0, 'text': 'My OK data'},
                    {'status': 1, 'text': 'My not OK data'}]
        >>> for token, text in lexer.tokenize(data):
                print '%-7s %s' % (token, repr(text))

        Ok      'My OK data'
        Fail    'My not OK data'
        >>>
        """
        data = self.preprocess(data)
        for t, v in self.lex(data):
            yield t, v

    @abc.abstractmethod
    def lex(self, data):
        """Return an iterable of (token, text) pairs.

        In subclasses, implement this method as a generator to
        maximize effectiveness.
        """


class RegexLexer(Lexer):
    """Base for simple stateful regular expression-based lexers.
    Simplifies the lexing process so that you need only
    provide a list of states and regular expressions.
    """

    # Flags for compiling the regular expressions.
    # Defaults to MULTILINE.
    flags = re.MULTILINE

    # Dict of {'state': [(regex, token, new_state), ...], ...}
    # The initial state is 'root'.
    config = {}

    def _get_tokens(self):
        tokens = {}
        for state, items in self.config.items():
            current_state = tokens[state] = []
            for regex, token, new_state in items:
                current_state.append((
                    re.compile(regex, self.flags).match,
                    token,
                    new_state
                ))
        return tokens

    def lex(self, text):
        """Do the lexical analysis"""
        tokens = self._get_tokens()
        state = 'root'
        pos = 0
        l = len(text)
        statetokens = tokens[state]
        while pos < l:
            for matcher, t, new_state in statetokens:
                m = matcher(text, pos)
                if m:
                    yield t, m.group()
                    pos = m.end()
                    if new_state is not None:
                        state = new_state
                        statetokens = tokens[state]
                    break
            else:
                state = 'root'
                statetokens = tokens['root']
                yield Token.Text, text[pos]
                pos += 1
