from typing import Any

from pydantic import BaseModel

from app.core.providers.base import LLMResponse


class EvaluatorInfo(BaseModel):
    evaluator_id: str
    description: str
    config_schema: dict[str, Any]


class EvaluatorConfig(BaseModel):
    """
    Configuration for a single evaluator.

    Attributes:
        evaluator_id (str): Unique identifier for the evaluator.
        weight (float): How much this evaluator's result should be weighted in an aggreagted result.
        threshold (float): The minimum score needed for this evaluation to be considered passing.
        config (dict[str, Any]): Arbitrary configuration options for the evaluator.
    """

    evaluator_id: str
    weight: float = 1
    threshold: float | None = None
    config: dict[str, Any]


class EvaluationRequest(BaseModel):
    """
    Request object containing the output to evaluate and the evaluator configurations.

    Attributes:
        model_output (str): The text or content which has been produced by some model that is to be evaluated.
        configs (list[EvaluatorConfig]): List of evaluator configurations to use.
    """

    model_output: str
    configs: list[EvaluatorConfig]


# TODO: introduce error result
class EvaluationResult(BaseModel):
    """
    Result of a single evaluator's evaluation.

    Attributes:
        evaluator_id (str): The ID of the evaluator that produced this result.
        passed (bool): Whether the output passed the evaluator's criteria.
        reasoning (str): A message that explains why the evaluation passed or failed.
        normalised_score (float): A score given by the evaluator that's between 0-1.
        execution_time (int): Evaluator execution time measured in ms.
        error (str | None): If something went wrong, this will contain an error message.
    """

    evaluator_id: str
    passed: bool = False
    reasoning: str | LLMResponse
    normalised_score: float = 0
    execution_time: int = 0
    error: str | None = None


class EvaluationResponse(BaseModel):
    """
    Response object containing the aggregated evaluation results.

    Attributes:
        weighted_average_score (float): The sum of each normalised_score multplied by it's corresponding weight divided by the sum of all the weights.
        results (list[EvaluationResult]): List of results from each evaluator.
    """

    weighted_average_score: float
    results: list[EvaluationResult]
