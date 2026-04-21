# based on https://dev.to/konstantinos_andreou_4dc1/tutorial-dynamic-class-discovery-and-loading-in-python-5dh8
import importlib
from pathlib import Path

from app.core.evaluators.base import BaseEvaluator


class EvaluatorLoader:
    # todo: docs for this class
    MODULE = "backend.app.core.evaluators"

    def __init__(self) -> None:
        # print( importlib.import_module(self.MODULE))
        self.module = importlib.import_module(self.MODULE)
        self.class_to_find = BaseEvaluator
        self._found_evaluators = self._evaluator_loader()

    def _evaluator_loader(self) -> dict[str, BaseEvaluator]:
        """
        Dynamically loads all evaluators from the module
        :return Dict[str, BaseEvaluator] # todo: improve this
        """
        found_evaluators: dict[str, BaseEvaluator] = {}
        root_dir = Path(self.module.__path__[0])
        # print(root_dir)
        for file in root_dir.glob("*.py"):
            if file.name.startswith("__") or file.name == "base.py" or file.name == "orchestrator.py":
                continue
            module_name = file.stem
            # print(module_name)
            module = importlib.import_module(self.MODULE + "." + module_name)
            # print(module)
            for evaluator in dir(module):
                # print("evaulator:", evaluator)
                # print(evaluator)
                obj = getattr(module, evaluator)
                # print("objects", obj)
                # print(BaseEvaluator)
                # print(obj, issubclass(obj, BaseEvaluator))
                if (
                    isinstance(obj, type)
                    and issubclass(obj, BaseEvaluator)
                    and obj is not BaseEvaluator
                ):
                    # print(evaluator)
                    found_evaluators[evaluator] = getattr(module, evaluator)
        return found_evaluators


def main() -> None:
    loader = EvaluatorLoader()

    for name, evaluator in loader._found_evaluators.items():
        print(name, evaluator)


if __name__ == "__main__":
    main()
