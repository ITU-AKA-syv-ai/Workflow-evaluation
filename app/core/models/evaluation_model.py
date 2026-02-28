from typing import Any

from pydantic import BaseModel


class EvaluatorInfo(BaseModel):
    evaluator_id: str
    description: str
    config_schema: dict[str, Any]


class EvaluatorConfig(BaseModel):
    """
    Configuration for a single evaluator.

    Attributes:
        evaluator_id (str): Unique identifier for the evaluator.
        config (dict[str, Any]): Arbitrary configuration options for the evaluator.
    """

    evaluator_id: str
    config: dict[str, Any]


class EvaluationRequest(BaseModel):
    """
    Request object containing the output to evaluate and the evaluator configurations.

    Attributes:
        output (str): The text or content to be evaluated.
        configs (list[EvaluatorConfig]): List of evaluator configurations to use.
    """

    output: str
    configs: list[EvaluatorConfig]


class EvaluationResult(BaseModel):
    """
    Result of a single evaluator's evaluation.

    Attributes:
        evaluator_id (str): The ID of the evaluator that produced this result.
        passed (bool): Whether the output passed the evaluator's criteria.
    """

    evaluator_id: str
    passed: bool
    error: str | None = None


class EvaluationResponse(BaseModel):
    """
    Response object containing all evaluation results.

    Attributes:
        results (list[EvaluationResult]): List of results from each evaluator.
    """

    results: list[EvaluationResult]
