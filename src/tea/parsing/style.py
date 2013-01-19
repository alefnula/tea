__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '19 January 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

from .token import STANDARD_TOKENS



class Font(object):
    '''Font properties'''

    Defalt    = 0
    
    # Style
    Mono      = 1
    Roman     = 2
    Sans      = 4
    
    # Decoration
    Bold      =  8
    Italic    = 16
    Underline = 32

    REPRS = {
        'mono'      : Mono,
        'roman'     : Roman,
        'sans'      : Sans,
        'bold'      : Bold,
        'italic'    : Italic,
        'underline' : Underline,
    }



class Style(object):    
    # overall background color (``None`` means transparent)
    background_color = None

    #: Style definitions for individual token types.
    styles = {}

    def __init__(self):
        for token in STANDARD_TOKENS:
            if token not in self.styles:
                self.styles[token] = ''
        
        self._styles = {}
        for token, styledef in self.styles.items():
            self._styles[token] = s = {
                'fg'     : None,
                'bg'     : None,
                'font'   : Font.Defalt,
                'border' : None
            }
            for part in styledef.split():
                if part[:3] == 'fg:':
                    s['fg'] = styledef[3:]
                elif part[:3] == 'bg:':
                    s['bg'] = styledef[3:]
                elif part in Font.REPRS:
                    s['font'] |= Font.REPRS[part]
                elif part[:7] == 'border:':
                    s['border'] = s[7:]
                else:
                    s['fg'] = part
        
    def style_for_token(self, token):
        return self._styles[token]
