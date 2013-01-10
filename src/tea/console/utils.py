__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '20 October 2010'
__copyright__ = 'Copyright (c) 2010 Viktor Kerkez'

from tea.system import platform

if platform.is_a(platform.WINDOWS | platform.DOTNET):
    import os
    import ctypes
    
    def _clear_screen(numlines):
        os.system('cls')
        
    def _getch():
        msvcrt = ctypes.cdll.msvcrt
        return chr(msvcrt._getch())

elif platform.is_a(platform.POSIX):
    import sys

    def _clear_screen(numlines):
        os.system('clear')
    
    def _getch():
        import tty, termios #@UnresolvedImport
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
else:
    raise platform.not_supported('tea.console.utils')


def clear_screen(numlines=100):
    '''Clear the console.
    
    @type  numlines: integer
    @param numlines: This is an optional argument used only as a fall-back if
        the operating system console doesn't have clear screen function.
    @rtype: None
    '''
    _clear_screen(numlines)


def getch():
    '''Crossplatfrom getch() function.
    
    Same as the getch function from msvcrt library, but works on all platforms.
    @rtype:  string
    @return: One character got from standard input.
    '''
    return _getch()
