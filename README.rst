tea
===

``tea`` is a set of cross-platform (Windows, POSIX, Mac OSX),
cross-interpreter (CPython 2.7, CPython 3.3, IronPython) libraries developed
for common tasks like executing and manipulating processes, sending emails,
file system manipulation, console output coloring and formatting, operating
system detection and cross-platform OS specific things handling, cross
platform cron jobs and a great number of utility functions that I caught
myself writing over and over again.

Also parts of the ``tea`` library can be viewed as a sand-box where I start
a module, which eventually, if it grows and become large enough to become a
library itself, gets extracted as a separate project.

Modules like ``ds`` (data structures), ``logger``, ``msg``, ``process``,
``shutil``, ``system``, ``utils``... will always remain a part of ``tea``.

Other modules, like ``commander`` (library for creating command line
applications) will eventually be extracted to it's own projects. 

Full documentation on `tea-lib.readthedocs.org`_.


.. _tea-lib.readthedocs.org: https://tea-lib.readthedocs.org
