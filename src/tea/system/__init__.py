__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '19 November 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import sys
_names = sys.builtin_module_names


class __platform(object):

    (POSIX, MAC, DARWIN, WINDOWS, WINDOWS_CE, DOTNET, OS2, RISCOS) = (
        1, 2, 4, 8, 16, 32, 64, 128
    )

    NAMES = {
        POSIX: 'POSIX',
        MAC: 'MAC',
        DARWIN: 'DARWIN',
        WINDOWS: 'Windows NT',
        WINDOWS_CE: 'Windows CE',
        DOTNET: '.NET',
        OS2: 'OS2',
        RISCOS: 'RISC OS'
    }

    ORDER = [DOTNET, DARWIN, POSIX, WINDOWS, OS2, MAC, WINDOWS_CE, RISCOS]

    class PlatformNotSupportedError(Exception):
        def __init__(self, platform, message):
            self.platform = platform
            self.message = message

        def __repr__(self):
            return 'PlatformNotSupportedError [%s]: %s' % (
                __platform.NAMES[self.platform], self.message
            )
        __str__ = __repr__

    def __init__(self):
        self.__platforms = 0
        self.__default = 0

        if 'posix' in _names:
            self.__platforms |= self.POSIX
        if 'mac' in _names:
            self.__platforms |= self.MAC
        if 'darwin' == sys.platform:
            self.__platforms |= self.DARWIN
        if 'nt' in _names:
            self.__platforms |= self.WINDOWS
        if 'ce' in _names:
            self.__platforms |= self.WINDOWS_CE
        if 'clr' in _names:
            self.__platforms |= self.DOTNET
        if 'os2' in _names:
            self.__platforms |= self.OS2
        if 'riscos' in _names:
            self.__platforms |= self.RISCOS
        for platform in self.ORDER:
            if self.__platforms & platform:
                self.__default = platform
                break

    def is_a(self, platforms):
        return (self.__platforms & platforms) > 0

    def is_only(self, platform):
        return (self.__platforms & platform) == self.__platforms

    def get_all(self):
        all_platforms = []
        for p in self.ORDER:
            if self.__platforms & p:
                all_platforms.append(p)
        return all_platforms

    def get_all_names(self):
        all_names = []
        for p in self.get_all():
            all_names.append(self.NAMES[p])
        return all_names

    @property
    def default(self):
        return self.__default

    def not_supported(self, module):
        return self.PlatformNotSupportedError(
            self.__default,
            '"%s" module is not supported on this platform!' % module
        )


platform = __platform()


if platform.is_a(platform.POSIX):
    from .posix_system import *
elif platform.is_a(platform.DOTNET):
    from .dotnet_system import *
elif platform.is_a(platform.WINDOWS):
    from .win_system import *
else:
    raise platform.not_supported('tea.system')
