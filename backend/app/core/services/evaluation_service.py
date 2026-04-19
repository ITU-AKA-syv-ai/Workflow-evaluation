from app.core.models.evaluation_model import EvaluatorInfo
from app.core.models.registry import EvaluationRegistry


def get_evaluators(reg: EvaluationRegistry) -> list[EvaluatorInfo]:
    """
    Retrieve all available evaluators from the registry.

    Returns:
        list[EvaluatorInfo]: A list of EvaluatorInfo objects, each containing the evaluator's ID, description, and
        configuration schema.
    """
    return [
        EvaluatorInfo(
            evaluator_id=evaluator.name,
            description=evaluator.description,
            config_schema=evaluator.config_schema,
        )
        for evaluator in reg.get_evaluators()
    ]
