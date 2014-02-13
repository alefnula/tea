__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '20 October 2010'
__copyright__ = 'Copyright (c) 2010 Viktor Kerkez'

import re
import sys
import ctypes

from tea.system import platform


class Color(object):
    black = 'black'
    blue = 'blue'
    green = 'green'
    cyan = 'cyan'
    red = 'red'
    purple = 'purple'
    yellow = 'yellow'
    gray = 'gray'
    white = 'white'
    normal = 'normal'

    @classmethod
    def colors(cls):
        return (cls.black,  cls.blue,   cls.green, cls.cyan,  cls.red,
                cls.purple, cls.yellow, cls.gray,  cls.white, cls.normal)

    @classmethod
    def color_re(cls):
        return re.compile(r'\[(?P<dark>dark\ )?(?P<color>%s)\]' %
                          '|'.join(cls.colors()), re.MULTILINE)


if platform.is_a(platform.WINDOWS | platform.DOTNET):

    def _set_color(fg, bg, fg_dark, bg_dark, underlined):
        # System is Windows
        STD_INPUT_HANDLE = -10
        STD_OUTPUT_HANDLE = -11
        STD_ERROR_HANDLE = -12
        # COLORS[fg or bg][is dark][color]
        COLORS = {
            'fg': {
                True: {Color.black: 0x00, Color.blue: 0x01, Color.green: 0x02,
                       Color.cyan: 0x03, Color.red: 0x04, Color.purple: 0x05,
                       Color.yellow: 0x06, Color.white: 0x07, Color.gray: 0x08,
                       Color.normal: 0x07},
                False: {Color.black: 0x00, Color.blue: 0x09, Color.green: 0x0A,
                        Color.cyan: 0x0B, Color.red: 0x0C, Color.purple: 0x0D,
                        Color.yellow: 0x0E, Color.white: 0x0F,
                        Color.gray: 0x07, Color.normal: 0x07}
            },
            'bg': {
                True: {Color.black: 0x00, Color.blue: 0x10, Color.green: 0x20,
                       Color.cyan: 0x30, Color.red: 0x40, Color.purple: 0x50,
                       Color.yellow: 0x60, Color.white: 0x70, Color.gray: 0x80,
                       Color.normal: 0x00},
                False: {Color.black: 0x00, Color.blue: 0x90, Color.green: 0xA0,
                        Color.cyan: 0xB0, Color.red: 0xC0, Color.purple: 0xD0,
                        Color.yellow: 0xE0, Color.white: 0xF0,
                        Color.gray: 0x70, Color.normal: 0x00}
            }
        }
        std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        code = 0 | COLORS['fg'][fg_dark][fg] | COLORS['bg'][bg_dark][bg]
        ctypes.windll.kernel32.SetConsoleTextAttribute(std_out_handle, code)


elif platform.is_a(platform.POSIX):

    def _set_color(fg, bg, fg_dark, bg_dark, underlined):
        COLORS = {
            'fg': {
                Color.black: 30, Color.red: 31, Color.green: 32,
                Color.yellow: 33, Color.blue: 34, Color.purple: 35,
                Color.cyan: 36, Color.gray: 37, Color.white: 37,
                Color.normal: 00,
            },
            'bg': {
                Color.black: 40, Color.red: 41, Color.green: 42,
                Color.yellow: 43, Color.blue:  44, Color.purple: 45,
                Color.cyan: 46, Color.gray: 47, Color.white: 47,
                Color.normal: 00,
            }
        }
        args = set()
        if fg != Color.normal:
            if not fg_dark:
                args.add(1)
            args.add(COLORS['fg'][fg])
        if bg != Color.normal:
            args.add(COLORS['bg'][bg])
        if underlined:
            args.add(4)
        # White and gray are special cases
        if fg == Color.white:
            args.add(1)
        if fg == Color.gray:
            if fg_dark:
                args.update([1, 30])
                args.remove(37)
            else:
                args.remove(1)
        sys.stdout.write('\33[%sm' % ';'.join(map(str, args)))

else:
    raise platform.not_supported('tea.console.color')


def set_color(fg=Color.normal, bg=Color.normal, fg_dark=False, bg_dark=False,
              underlined=False):
    """Set the console color.

    >>> set_color(Color.red, Color.blue)
    >>> set_color('red', 'blue')
    >>> set_color() # returns back to normal
    """
    _set_color(fg, bg, fg_dark, bg_dark, underlined)


def strip_colors(text):
    """Helper function used to strip out the color tags so other function can
    determine the real text line lengths.

    :param str text: Text to strip color tags from
    :rtype: :obj:`str`
    :return: Stripped text.
    """
    return Color.color_re().sub('', text)


def cprint(text, fg=Color.normal, bg=Color.normal, fg_dark=False,
           bg_dark=False, underlined=False, parse=False):
    """Prints string in to stdout using colored font.

    See L{set_color} for more details about colors.

    :type  color: str or list[str]
    :param color: If color is a string than this is a color in which the text
                  will appear. If color is a list of strings than all desired
                  colors will be used as a mask (this is used when you wan to
                  set foreground and background color).
    :param str text: Text that needs to be printed.
    """
    if parse:
        color_re = Color.color_re()
        lines = text.splitlines()
        count = len(lines)
        for i, line in enumerate(lines):
            previous = 0
            end = len(line)
            for match in color_re.finditer(line):
                sys.stdout.write(line[previous:match.start()])
                d = match.groupdict()
                set_color(d['color'],
                          fg_dark=False if d['dark'] is None else True)
                previous = match.end()
            sys.stdout.write(line[previous:end] + ('\n' if (i < (count - 1) or
                             text[-1] == '\n') else ''))
    else:
        set_color(fg, bg, fg_dark, bg_dark, underlined)
        sys.stdout.write(text)
        set_color()


def colorize_output(output, colors, indent=0):
    """Prints output to console using provided color mappings.

    Color mapping is dict with regular expressions as key and tuple of two as
    values. Key is used to match if line should be colorized and tuple contains
    color to be used and boolean value that indicates if dark foreground
    is used.
    For example:

        >>> CLS = {
        >>>     re.compile(r'^(--- .*)$'): (Color.red, False)
        >>> }

    will colorize lines that start with '---' to red.

    If different parts of line needs to be in different color then dict must be
    supplied in colors with keys that are named group from regular expression
    and values that are tuples of color and boolean that indicates if dark
    foreground is used.
    For example:

        >>> CLS = {
        >>>     re.compile(r'^(?P<key>user:\s+)(?P<user>.*)$'): {
        >>>         'key': (Color.yellow, True),
        >>>         'user': (Color.cyan,   False)
        >>>     }
        >>> }

    will colorize line 'user: Some user' so that 'user:' part is yellow with
    dark foreground and 'Some user' part is cyan without dark foreground.
    """
    for line in output.split('\n'):
        cprint(' ' * indent)
        if line == '':
            cprint('\n')
            continue
        for regexp, color_def in colors.items():
            if regexp.match(line) is not None:
                _colorize_single_line(line, regexp, color_def)
                break
        else:
            cprint('%s\n' % line)


def _colorize_single_line(line, regexp, color_def):
    """Prints single line to console with ability to colorize only parts of
    line.
    """
    match = regexp.match(line)
    groupdict = match.groupdict()
    groups = match.groups()
    if not groupdict:
        # no named groups, just colorize whole line
        color = color_def[0]
        dark = color_def[1]
        cprint('%s\n' % line, color, fg_dark=dark)
    else:
        rev_groups = {v: k for k, v in groupdict.items()}
        for part in groups:
            if part in rev_groups and rev_groups[part] in color_def:
                group_name = rev_groups[part]
                cprint(part, color_def[group_name][0],
                       fg_dark=color_def[group_name][1])
            else:
                cprint(part)
        cprint('\n')
