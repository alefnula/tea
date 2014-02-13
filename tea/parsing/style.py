__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '19 January 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

from tea.console.color import Color


class Font(object):
    """Font properties"""

    Defalt = 0

    # Style
    Mono = 1
    Roman = 2
    Sans = 4

    # Decoration
    Bold = 8
    Italic = 16
    Underline = 32

    REPRS = {
        'mono': Mono,
        'roman': Roman,
        'sans': Sans,
        'bold': Bold,
        'italic': Italic,
        'underline': Underline,
    }


class Style(object):
    # overall background color (``None`` means transparent)
    background_color = None

    # Cached parsed styles - do not touch this
    _cache = {}

    # Style definitions for individual token types.
    styles = {}

    @staticmethod
    def _parse_style(style):
        s = {
            'fg': None,
            'bg': None,
            'font': Font.Defalt,
            'border': None
        }
        for part in style.split():
            if part[:3] == 'fg:':
                s['fg'] = part[3:]
            elif part[:3] == 'bg:':
                s['bg'] = part[3:]
            elif part in Font.REPRS:
                s['font'] |= Font.REPRS[part]
            elif part[:7] == 'border:':
                s['border'] = part[7:]
            else:
                s['fg'] = part
        return s

    @classmethod
    def get(cls, token):
        """Searches the whole inheritance three for a token style.

        If it doesn't find it return an empty style.
        """
        # First look into the cache
        if token not in cls._cache:
            for klass in cls.mro()[:-1]:  # Do not search in object
                if token in klass.styles:
                    cls._cache[token] = cls._parse_style(klass.styles[token])
                    break
            else:
                cls._cache[token] = cls._parse_style('')
        return cls._cache[token]


class StyleAdapter(object):
    """Style adapter is a helper class for adapting a style for restricted
    environments, where not all colors or font styles are available.

    For example the terminal console doesn't have the full range of colors
    and also doesn't have font styles. Look in the ConsoleStyleAdapter for
    example implementation.
    """
    def __init__(self, style):
        self.style = style

    def adapt(self, style):
        """Override this method to implement the adaptation logic"""
        return style

    def get(self, token):
        return self.adapt(self.style.get(token))


class ConsoleStyleAdapter(StyleAdapter):
    """Simple hex color to console color adapter"""

    def __init__(self, *args, **kwargs):
        super(ConsoleStyleAdapter, self).__init__(*args, **kwargs)
        self._cache = {}

    def _adapt_color(self, color):
        r, g, b = int(color[:2], 16), int(color[2:4], 16), int(color[4:], 16)
        # Black
        if r <= 64 and g <= 64 and b <= 64:
            return (Color.black, False)
        # Blue
        elif r <= 64 and g <= 64 and b <= 128:
            return (Color.blue, True)
        elif r <= 64 and g <= 64:
            return (Color.blue, False)
        # Green
        elif r <= 64 and b <= 64 and g <= 128:
            return (Color.green, True)
        elif r <= 64 and b <= 64:
            return (Color.green, False)
        # Red
        elif b <= 64 and g <= 64 and r <= 128:
            return (Color.red, True)
        elif b <= 64 and g <= 64:
            return (Color.red, False)
        # Cyan
        elif r <= 64 and g <= 128 and b <= 128:
            return (Color.cyan, True)
        elif r <= 64 and g > 128 and b > 128:
            return (Color.cyan, False)
        # Purple
        elif g <= 64 and r <= 128 and b <= 128:
            return (Color.purple, True)
        elif g <= 64 and r > 128 and b > 128:
            return (Color.purple, False)
        # Yellow
        elif b <= 64 and r <= 128 and g <= 128:
            return (Color.yellow, True)
        elif b <= 64 and r > 128 and g > 128:
            return (Color.yellow, False)
        # White
        elif r > 192 and g > 192 and b > 192:
            return (Color.white,  False)
        # Gray
        elif abs(r - g) < 64 and abs(r - b) < 64 and abs(g - b) < 64:
            if r <= 128 and g <= 128 and b <= 128:
                return (Color.gray, True)
            else:
                return (Color.gray, False)
        return (Color.normal, False)

    def _get_color(self, color):
        if color is None:
            return (Color.normal, False)
        if color[0] == '#':
            color = color[1:]
        if color not in self._cache:
            self._cache[color] = self._adapt_color(color)
        return self._cache[color]

    def adapt(self, style):
        return {
            'fg': self._get_color(style['fg']),
            'bg': self._get_color(style['bg']),
            'font': Font.Defalt,
            'border': None,
        }
