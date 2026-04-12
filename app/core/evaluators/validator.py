from app.core.models.evaluation_model import EvaluationRequest
from app.core.models.registry import EvaluationRegistry
from app.exceptions import NoEvaluatorsSpecifiedError, UnknownEvaluatorsError


class EvaluationRequestValidator:
    def validate(self, request: EvaluationRequest, registry: EvaluationRegistry) -> None:

        if not request.configs:
            raise NoEvaluatorsSpecifiedError()

        reg_ids = {e.name for e in registry.get_evaluators()}
        req_ids = {c.evaluator_id for c in request.configs}

        id_diff = req_ids - reg_ids
        if id_diff:
            raise UnknownEvaluatorsError(sorted(id_diff))
