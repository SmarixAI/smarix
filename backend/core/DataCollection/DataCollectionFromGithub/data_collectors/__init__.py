# python
# File: backend/core/DataCollection/DataCollectionFromGithub/data_collectors/__init__.py
import pkgutil
from importlib import import_module

__all__ = []

# Dynamically import all sibling modules (every .py in this package except __init__.py)
for _finder, name, _ispkg in pkgutil.iter_modules(__path__):
    module = import_module(f".{name}", package=__name__)
    globals()[name] = module
    __all__.append(name)
