from __future__ import print_function

__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '20 October 2010'
__copyright__ = 'Copyright (c) 2010 Viktor Kerkez'

import os
import re
import sys
from textwrap import TextWrapper

# tea imports
from .color import strip_colors, set_color


def format_page(text):
    """Formats the text for output adding ASCII frame around the text.

    :param str text: Text that needs to be formatted.
    :rtype:  string
    :return: Formatted string.
    """
    width = max(map(len, text.splitlines()))
    page = '+-' + '-' * width + '-+\n'
    for line in text.splitlines():
        page += '| ' + line.ljust(width) + ' |\n'
    page += '+-' + '-' * width + '-+\n'
    return page


def table(text):
    """Formats the text as a table

    Text in format:

    first | second
    row 2 col 1 | 4

    Will be formatted as::

        +-------------+--------+
        | first       | second |
        +-------------+--------+
        | row 2 col 1 | 4      |
        +-------------+--------+

    :param str text: Text that needs to be formatted.
    :rtype:  str
    :return: Formatted string.
    """
    table_bar = (lambda col_lengths:
                 '+-%s-+%s' % ('-+-'.join(['-' * length
                                           for length in col_lengths]),
                               os.linesep))
    rows = []
    for line in text.splitlines():
        rows.append([part.strip() for part in line.split('|')])
    max_cols = max(map(len, rows))
    col_lengths = [0] * max_cols
    for row in rows:
        cols = len(row)
        if cols < max_cols:
            row.extend([''] * (max_cols - cols))
        for i, col in enumerate(row):
            col_length = len(col)
            if col_length > col_lengths[i]:
                col_lengths[i] = col_length
    text = table_bar(col_lengths)
    for i, row in enumerate(rows):
        cols = []
        for i, col in enumerate(row):
            cols.append(col.ljust(col_lengths[i]))
        text += '| %s |%s' % (' | '.join(cols), os.linesep)
        text += table_bar(col_lengths)
    return text


def hbar(width):
    """Returns ASCII HBar ``+---+`` with the specified width.

    :param int width: Width of the central part of the bar.
    :rtype:  str
    :return: ASCII HBar.
    """
    return '+-' + '-' * width + '-+'


def print_page(text):
    """Formats the text and prints it on stdout.

    Text is formatted by adding a ASCII frame around it and coloring the text.
    Colors can be added to text using color tags, for example:

        My [FG_BLUE]blue[NORMAL] text.
        My [BG_BLUE]blue background[NORMAL] text.
    """
    color_re = re.compile(r'\[(?P<color>[FB]G_[A-Z_]+|NORMAL)\]')
    width = max([len(strip_colors(x)) for x in text.splitlines()])
    print('\n' + hbar(width))
    for line in text.splitlines():
        if line == '[HBAR]':
            print(hbar(width))
            continue
        tail = width - len(strip_colors(line))
        sys.stdout.write('| ')
        previous = 0
        end = len(line)
        for match in color_re.finditer(line):
            sys.stdout.write(line[previous:match.start()])
            set_color(match.groupdict()['color'])
            previous = match.end()
        sys.stdout.write(line[previous:end])
        sys.stdout.write(' ' * tail + ' |\n')
    print(hbar(width))


def wrap_text(text, width=80):
    """Wraps text lines to maximum *width* characters.

    Wrapped text is aligned against the left text border.

    :param str text: Text to wrap.
    :param int width: Maximum number of characters per line.
    :rtype:  str
    :return: Wrapped text.
    """
    text = re.sub('\s+', ' ', text).strip()
    wrapper = TextWrapper(width=width, break_long_words=False,
                          replace_whitespace=True)
    return wrapper.fill(text)


def rjust_text(text, width=80, indent=0, subsequent=None):
    """Same as L{wrap_text} with the difference that the text is aligned
    against the right text border.

    :param str text: Text to wrap and align.
    :param int width: Maximum number of characters per line.
    :param int indent: Indentation of the first line.
    :type  subsequent: int or None
    :param subsequent: Indentation of all other lines, if it is None, then the
        indentation will be same as for the first line.
    """
    text = re.sub('\s+', ' ', text).strip()
    if subsequent is None:
        subsequent = indent
    wrapper = TextWrapper(width=width, break_long_words=False,
                          replace_whitespace=True,
                          initial_indent=' ' * (indent + subsequent),
                          subsequent_indent=' ' * subsequent)
    return wrapper.fill(text)[subsequent:]


def center_text(text, width=80):
    """Center all lines of the text.

    It is assumed that all lines width is smaller then B{width}, because the
    line width will not be checked.

    :param str text: Text to wrap.
    :param int width: Maximum number of characters per line.
    :rtype:  str
    :return: Centered text.
    """
    centered = []
    for line in text.splitlines():
        centered.append(line.center(width))
    return '\n'.join(centered)
