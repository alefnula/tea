import logging
from re import sub
from html import parser


logger = logging.getLogger(__name__)


class _StripTagsParser(parser.HTMLParser):
    def __init__(self):
        super(_StripTagsParser, self).__init__()
        self.__text = []

    def handle_data(self, data):
        text = data.strip()
        if len(text) > 0:
            text = sub("[ \t\r\n]+", " ", text)
            self.__text.append(text + " ")

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.__text.append("\n\n")
        elif tag == "br":
            self.__text.append("\n")

    def handle_startendtag(self, tag, attrs):
        if tag == "br":
            self.__text.append("\n\n")

    def text(self):
        return "".join(self.__text).strip()


def strip_tags(html):
    try:
        p = _StripTagsParser()
        p.feed(html)
        p.close()
        return p.text()
    except Exception as e:
        logger.debug("Failed to strip tags. Error: %s", e)
        return html
