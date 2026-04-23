# based on https://dev.to/konstantinos_andreou_4dc1/tutorial-dynamic-class-discovery-and-loading-in-python-5dh8
import importlib
from pathlib import Path
from typing import TypeVar

from app.core.evaluators.base import BaseEvaluator

T = TypeVar("T", bound=BaseEvaluator)


class BaseDynamicRegister:
    """
    Base class for dynamically discovering classes from a module.
    This class scans a given directory, import all Python files not in the exclude_files
    and collect all subclasses of a specified base class.

    Attributes:
         MODULE (str): dot-path to the module/directory that should be scanned
         module: imported Python module object.
         class_to_find (type[T]): Base class used to filter discovered classes
         exclude_files (set[str]): List of files that should be ignored during scanning
         _found_classes (dict[str, type[T]]): Discovered classes mapped by class name.
    """
    MODULE: str

    def __init__(self, class_to_find: type[T], exclude_files: set[str]) -> None:
        self.module = importlib.import_module(self.MODULE)
        self.class_to_find = class_to_find
        self.exclude_files = exclude_files
        self._found_classes = self._dynamic_loader()

    def _dynamic_loader(self) -> dict[str, T]:
        """
        Dynamically discovers and loads all valid subclasses from the target module/directory

        Returns:
            dict[str, type[T]]: Discovered classes mapped by class name
        """
        found_classes: dict[str, T] = {}
        root_dir = Path(self.module.__path__[0])
        for file in root_dir.glob("*.py"):
            if file.name.startswith("__") or file.name in self.exclude_files:
                continue
            module_name = file.stem
            module = importlib.import_module(self.MODULE + "." + module_name)
            for name in dir(module):
                obj = getattr(module, name)
                if (
                    isinstance(obj, type)
                    and issubclass(obj, self.class_to_find)
                    and obj is not self.class_to_find
                ):
                    found_classes[name] = obj
        return found_classes
