import types
import pkgutil
import logging
from tea.utils import get_object


logger = logging.getLogger(__name__)


def anotate(name):
    """Annotate an object with a name."""

    def decorator(obj):
        setattr(obj, "_tea_ds_plugin", name)
        return obj

    return decorator


def load_plugins(modules, cls=None, annotation=None, subclasses=False):
    if cls is None and annotation is None:
        logger.warning(
            "Either the cls or the annotation has to be provided "
            "to the load_plugins function."
        )
        return []
    if not isinstance(modules, (list, tuple)):
        modules = [modules]
    # First load all the modules
    loaded_modules = []
    for module in modules:
        if not isinstance(module, types.ModuleType):
            module = get_object(module)
        loaded_modules.append(module)
        for (loader, module_name, is_pkg) in pkgutil.walk_packages(
            module.__path__
        ):
            loaded_modules.append(
                loader.find_module(module_name).load_module(module_name)
            )
    # If cls is provided then check the classes
    if cls is not None:
        if subclasses:
            classes = []

            def _get_sublasses(cls):
                for c in cls.__subclasses__():
                    classes.append(c)
                    _get_sublasses(c)

            _get_sublasses(cls)
            return classes
        else:
            return cls.__subclasses__()
    # If annotation is provided then check the annotations
    if annotation is not None:
        items = []
        for module in loaded_modules:
            for obj in module.__dict__.values():
                if getattr(obj, "_tea_ds_plugin", None) == annotation:
                    items.append(obj)
        return items
