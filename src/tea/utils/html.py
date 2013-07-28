__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '25 October 2010'
__copyright__ = 'Copyright (c) 2010 Viktor Kerkez'

from re import sub
try:
    from HTMLParser import HTMLParser   # py2
except ImportError:
    from html.parser import HTMLParser  # py3


class _StripTagsParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.__text = []

    def handle_data(self, data):
        text = data.strip()
        if len(text) > 0:
            text = sub('[ \t\r\n]+', ' ', text)
            self.__text.append(text + ' ')

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.__text.append('\n\n')
        elif tag == 'br':
            self.__text.append('\n')

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            self.__text.append('\n\n')

    def text(self):
        return ''.join(self.__text).strip()


def strip_tags(html):
    try:
        parser = _StripTagsParser()
        parser.feed(html)
        parser.close()
        return parser.text()
    except:
        return html
