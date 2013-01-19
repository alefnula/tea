__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '19 January 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import re

from . import token


class Lexer(object):
    def __init__(self):
        pass

    def preprocess(self, text):
        return text

    def get_tokens(self, text):
        '''Return an iterable of (tokentype, value) pairs generated from
        `text`.
        '''
        text = self.preprocess(text)
        for t, v in self.lex(text):
            yield t, v

    def lex(self, text):
        '''
        Return an iterable of (tokentype, value) pairs.
        In subclasses, implement this method as a generator to
        maximize effectiveness.
        '''
        raise NotImplementedError()



class RegexLexer(Lexer):
    '''
    Base for simple stateful regular expression-based lexers.
    Simplifies the lexing process so that you need only
    provide a list of states and regular expressions.
    '''

    # Flags for compiling the regular expressions.
    # Defaults to MULTILINE.
    flags = re.MULTILINE

    # Dict of {'state': [(regex, tokentype, new_state), ...], ...}
    #
    # The initial state is 'root'.
    tokens = {}

    def __init__(self):
        self._tokens = {}
        for state, items in self.tokens.items():
            current_state = self._tokens[state] = []
            for regex, token, new_state in items:
                current_state.append((
                    re.compile(regex, self.flags).match,
                    token,
                    new_state
                ))

    def lex(self, text):
        '''Do the lexical analisys'''
        state = 'root'
        pos = 0
        l   = len(text)
        statetokens = self._tokens[state]
        while pos < l:
            for matcher, t, new_state in statetokens:
                m = matcher(text, pos)
                if m:
                    yield t, m.group()
                    pos = m.end()
                    if new_state is not None:
                        state = new_state
                        statetokens = self._tokens[state]
                    break
            else:
                state = 'root'
                statetokens = self._tokens['root']
                yield token.Text, text[pos]
                pos += 1
