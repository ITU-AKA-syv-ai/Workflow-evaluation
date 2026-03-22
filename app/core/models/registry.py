from app.core.models.base import BaseEvaluator
from app.core.models.length_evaluator import LengthEvaluator
from app.core.models.substring_evaluator import SubstringEvaluator


class EvaluationRegistry:
    """
    A registry system for storing and retrieving evaluators using unique ids

    NOTE: This is a placeholder and will be replaced once this PBI is done: https://app.plane.so/ituxakaxsyvai/browse/ITUXA-36/

    Attributes:
        registry (dict[str, BaseEvaluator]): Dictionary which maps evaluator ID to an instance of that evaluator
    """

    registry: dict[str, BaseEvaluator]

    def __init__(self) -> None:
        self.registry: dict[str, BaseEvaluator] = {}
        """        Initialize an empty evaluation registry.
        """

    def get(self, id: str) -> BaseEvaluator | None:
        """
        Retrieve a registered evaluator by its unique ID.

        Args:
            id (str): The unique identifier of the evaluator.

        Returns:
            BaseEvaluator | None:
                The evaluator instance associated with the given ID,
                or None if no evaluator is registered under that ID.
        """
        if id in self.registry:
            return self.registry[id]
        return None

    def register(
        self, id: str, evaluator: BaseEvaluator
    ) -> bool:  # When the registry PBI(ITUXA-36) is done, this return type should be more descriptive as to what went wrong
        """
        Register a new evaluator under a unique ID.

        If an evaluator already exists under the given ID, it will not be overwritten.

        Args:
            id (str): The unique identifier for the evaluator.
            evaluator (BaseEvaluator): An instance of a BaseEvaluator subclass.

        Returns:
            bool: True if the evaluator was successfully registered, else false
        """
        if id in self.registry:
            return False
        self.registry[id] = evaluator
        return True


registry = EvaluationRegistry()
registry.register(LengthEvaluator().name, LengthEvaluator())
registry.register(SubstringEvaluator().name, SubstringEvaluator())
