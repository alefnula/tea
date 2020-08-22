import sys
import types
import logging
import pkgutil
import importlib
import traceback


logger = logging.getLogger(__name__)


def _package(module):
    """Hack for python2 since it does not have __package__ always set up.

    Args:
        module: Module for which we want the package name
    Returns:
        str: Model's package name
    """
    return (
        module.__name__ if module.__package__ is None else module.__package__
    )


def get_object(path="", obj=None):
    """Return an object from a dot path.

    Path can either be a full path, in which case the `get_object` function
    will try to import the modules in the path and follow it to the final
    object. Or it can be a path relative to the object passed in as the second
    argument.

    Args:
        path (str): Full or relative dot path to the desired object
        obj (object): Starting object. Dot path is calculated relatively to
            this object.

    Returns:
        Object at the end of the path, or list of non hidden objects if we use
        the star query.

    Example for full paths::

        >>> get_object('os.path.join')
        <function join at 0x1002d9ed8>
        >>> get_object('tea.process')
        <module 'tea.process' from 'tea/process/__init__.pyc'>

    Example for relative paths when an object is passed in::

        >>> import os
        >>> get_object('path.join', os)
        <function join at 0x1002d9ed8>

    Example for a star query. (Star query can be used only as the last element
    of the path::

        >>> get_object('tea.dsa.*')
        []
        >>> get_object('tea.dsa.singleton.*')
        [<class 'tea.dsa.singleton.Singleton'>,
         <class 'tea.dsa.singleton.SingletonMetaclass'>
         <module 'six' from '...'>]
        >>> get_object('tea.dsa.*')
        [<module 'tea.dsa.singleton' from '...'>]    # Since we imported it
    """
    if not path:
        return obj
    path = path.split(".")
    if obj is None:
        obj = importlib.import_module(path[0])
        path = path[1:]
    for item in path:
        if item == "*":
            # This is the star query, returns non hidden objects
            return [
                getattr(obj, name)
                for name in dir(obj)
                if not name.startswith("__")
            ]
        if isinstance(obj, types.ModuleType):
            submodule = "{}.{}".format(_package(obj), item)
            try:
                obj = importlib.import_module(submodule)
            except Exception as import_error:
                try:
                    obj = getattr(obj, item)
                except Exception:
                    # FIXME: I know I should probably merge the errors, but
                    #        it's easier just to throw the import error since
                    #        it's most probably the one user wants to see.
                    #        Create a new LoadingError and throw a combination
                    #        of the import error and attribute error.
                    raise import_error
        else:
            obj = getattr(obj, item)
    return obj


class Loader(object):
    """Module loader class loads recursively a module and all it's submodules.

    Loaded modules will be stored in the ``modules`` attribute of the loader as
    a dictionary of {module_path: module} key, value pairs.

    Errors accounted during the loading process will not stop the loading
    process. They will be stored in the ``errors`` attribute of the loader as a
    dictionary of {module_path: exception} key, value pairs.

    Usage::

        loader = Loader()
        loader.load('foo')
        loader.load('baz.bar', 'boo')

        import baz
        loader.load(baz)
    """

    def __init__(self):
        self.modules = {}
        self.errors = {}

    def load(self, *modules):
        """Load one or more modules.

        Args:
            modules: Either a string full path to a module or an actual module
                object.
        """
        for module in modules:
            if isinstance(module, str):
                try:
                    module = get_object(module)
                except Exception as e:
                    self.errors[module] = e
                    continue
            self.modules[module.__package__] = module
            for (loader, module_name, is_pkg) in pkgutil.walk_packages(
                module.__path__
            ):
                full_name = "{}.{}".format(_package(module), module_name)
                try:
                    self.modules[full_name] = get_object(full_name)
                    if is_pkg:
                        self.load(self.modules[full_name])
                except Exception as e:
                    self.errors[full_name] = e


def load_subclasses(klass, modules=None):
    """Load recursively all all subclasses from a module.

    Args:
        klass (str or list of str): Class whose subclasses we want to load.
        modules: List of additional modules or module names that should be
            recursively imported in order to find all the subclasses of the
            desired class. Default: None

    FIXME: This function is kept only for backward compatibility reasons, it
        should not be used. Deprecation warning should be raised and it should
        be replaces by the ``Loader`` class.
    """
    if modules:
        if isinstance(modules, str):
            modules = [modules]
        loader = Loader()
        loader.load(*modules)
    return klass.__subclasses__()


def get_exception():
    """Return full formatted traceback as a string."""
    trace = ""
    exception = ""
    exc_list = traceback.format_exception_only(
        sys.exc_info()[0], sys.exc_info()[1]
    )
    for entry in exc_list:
        exception += entry
    tb_list = traceback.format_tb(sys.exc_info()[2])
    for entry in tb_list:
        trace += entry
    return "%s\n%s" % (exception, trace)


def cmp(x, y):
    """Compare function from python2."""
    return (x > y) - (x < y)
