__author__ = "Viktor Kerkez <alefnula@gmail.com>"
__date__ = "20 October 2010"
__copyright__ = "Copyright (c) 2010 Viktor Kerkez"

import os
from tea.system import platform

if platform.is_a(platform.WINDOWS | platform.DOTNET):
    import msvcrt

    def _clear_screen(num_lines=100):
        os.system("cls")

    _getch = msvcrt.getch

elif platform.is_a(platform.POSIX):
    import sys

    def _clear_screen(num_lines=100):
        os.system("clear")

    def _getch():
        import tty
        import termios

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


else:
    raise platform.not_supported("tea.console.utils")


def clear_screen(num_lines=100):
    """Clear the console.

    Args:
        num_lines (int): This is an optional argument used only as a fall-back
            if the operating system console doesn't have clear screen function.
    """
    _clear_screen(num_lines)


def getch():
    """Get a character from standard input.

    Cross-platform getch() function.

    It's the same as the getch function from msvcrt library, but works on all
    platforms.

    Returns:
        str: One character got from standard input.
    """
    return _getch()
