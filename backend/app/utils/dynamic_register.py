# based on https://dev.to/konstantinos_andreou_4dc1/tutorial-dynamic-class-discovery-and-loading-in-python-5dh8
import importlib
from pathlib import Path
from typing import TypeVar

from app.core.evaluators.base import BaseEvaluator

T = TypeVar("T", bound=BaseEvaluator)


class BaseDynamicRegister:
    # todo: docs for this class
    MODULE: str  # MODULE = "backend.app.core.evaluators"

    def __init__(self, class_to_find: type[T], exclude_files: list[str]) -> None:
        # print( importlib.import_module(self.MODULE))
        self.module = importlib.import_module(self.MODULE)
        self.class_to_find = class_to_find
        self._found_evaluators = self._dynamic_loader()
        self.exclude_files = exclude_files

    def _dynamic_loader(self) -> dict[str, T]:
        """
        Dynamically loads all evaluators from the module
        :return Dict[str, BaseEvaluator] # todo: improve this
        """
        found_classes: dict[str, T] = {}
        root_dir = Path(self.module.__path__[0])
        # print(root_dir)
        for file in root_dir.glob("*.py"):
            if file.name.startswith("__") or file.name in self.exclude_files:  # file.name == "base.py" or file.name == "orchestrator.py":
                continue
            module_name = file.stem
            # print(module_name)
            module = importlib.import_module(self.MODULE + "." + module_name)
            # print(module)
            for name in dir(module):
                # print("evaulator:", evaluator)
                # print(evaluator)
                obj = getattr(module, name)
                # print("objects", obj)
                # print(BaseEvaluator)
                # print(obj, issubclass(obj, BaseEvaluator))
                if (
                    isinstance(obj, type)
                    and issubclass(obj, self.class_to_find)
                    and obj is not self.class_to_find
                ):
                    # print(evaluator)
                    found_classes[name] = obj
        return found_classes
