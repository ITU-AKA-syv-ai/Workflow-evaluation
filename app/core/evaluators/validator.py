from app.core.models.evaluation_model import EvaluationRequest
from app.core.models.registry import EvaluationRegistry
from app.exceptions import NoEvaluatorsSpecifiedError, UnknownEvaluatorsError


class EvaluationRequestValidator:
    """Validates an EvaluationRequest against a given EvaluationRegistry."""
    def validate(self, request: EvaluationRequest, registry: EvaluationRegistry) -> None:
        """
        Validate an evaluation request against the registered evaluators.

        Checks that the request specifies at least one evaluator config, and that
        all requested evaluator IDs exist in the registry.

        Args:
            request: The evaluation request containing evaluator configs to validate.
            registry: The registry of known evaluators to validate against.

        Raises:
            NoEvaluatorsSpecifiedError: If request.configs is empty.
            UnknownEvaluatorsError: If any evaluator ID in the request is not
                registered, containing the unknown IDs in sorted order.
        """

        if not request.configs:
            raise NoEvaluatorsSpecifiedError()

        reg_ids = {e.name for e in registry.get_evaluators()}
        req_ids = {c.evaluator_id for c in request.configs}

        id_diff = req_ids - reg_ids
        if id_diff:
            raise UnknownEvaluatorsError(sorted(id_diff))
