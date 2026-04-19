from app.core.evaluators.base import BaseEvaluator


class EvaluationRegistry:
    """
    A registry system for storing and retrieving evaluators using unique ids

    NOTE: This is a placeholder and will be replaced once this PBI is done: https://app.plane.so/ituxakaxsyvai/browse/ITUXA-36/

    Attributes:
        registry (dict[str, BaseEvaluator]): Dictionary which maps evaluator ID to an instance of that evaluator
    """

    _registry: dict[str, BaseEvaluator]

    def __init__(self) -> None:
        """
        Initialize an empty evaluation registry.
        """
        self._registry: dict[str, BaseEvaluator] = {}
        # self._registry = {}

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
    ):  # When the registry PBI(ITUXA-36) is done, this return type should be more descriptive as to what went wrong
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
