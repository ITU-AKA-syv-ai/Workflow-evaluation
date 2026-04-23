from app.config.settings import get_settings
from app.core.evaluators.base import BaseEvaluator
from backend.app.utils.dynamic_register import BaseDynamicRegister


class EvaluationRegistry(BaseDynamicRegister):
    """
    A registry system for discovering, instantiating and retrieving evaluators using unique ids

    This class extends BaseDynamicRegister to dynamically load subclasses of the BaseEvaluator class
    from the evaluators directory.

    Attributes:
        MODULE (str): The path of the module/directory where evaluator classes are discovered.
        _registry (dict[str, BaseEvaluator]): Dictionary which maps evaluator ID to an instance of that evaluator
        _found_classes (dict[str, type[BaseEvaluator]]): Discovered evaluator classes.
    """

    _registry: dict[str, BaseEvaluator]
    MODULE = "app.core.evaluators"

    def __init__(self) -> None:
        """
        Initialize an empty evaluation registry. # todo: update
        """
        super().__init__(class_to_find=BaseEvaluator, exclude_files={"base.py", "cosine_evaluator.py", "llm_judge.py", "rouge_evaluator.py", "orchestrator.py"})  # todo: not pretty
        self._registry: dict[str, BaseEvaluator] = {}
        self.register_instances()

    def register_instances(self) -> None:
        """
        Instantiate and register all registered evaluator classes.
        """
        settings = get_settings()
        for _, found in self._found_classes.items():
            evaluator = found(settings.threshold)
            self.register(evaluator.name, evaluator)

    def get_evaluators(self) -> list[BaseEvaluator]:
        return list(self._registry.values())

    def get(self, id: str) -> BaseEvaluator:
        """
        Retrieve a registered evaluator by its unique ID.

        Args:
            id (str): The unique identifier of the evaluator.

        Returns:
            BaseEvaluator: The evaluator instance associated with the given ID.

        Raises:
            KeyError: If no evaluator is registered under the given ID.
        """
        if id not in self._registry:
            raise KeyError(f"Evaluator '{id}' not found")  # this should never happen
        return self._registry[id]

    def register(
        self, id: str, evaluator: BaseEvaluator
    ) -> (
        bool
    ):  # When the registry PBI(ITUXA-36) is done, this return type should be more descriptive as to what went wrong # todo: Error handling
        """
        Register a new evaluator under a unique ID.

        If an evaluator already exists under the given ID, it will not be overwritten.

        Args:
            id (str): The unique identifier for the evaluator.
            evaluator (BaseEvaluator): An instance of a BaseEvaluator subclass.

        Returns:
            bool: True if the evaluator was successfully registered, else false
        """
        if id in self._registry:
            return False
        self._registry[id] = evaluator
        return True
