from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.providers.base import LLMResponse
from app.core.services.job_status_service import JobStatus


class EvaluatorInfo(BaseModel):
    evaluator_id: str
    description: str
    config_schema: dict[str, Any]


class EvaluatorConfig(BaseModel):
    """
    Configuration for a single evaluator.

    Attributes:
        evaluator_id (str): Unique identifier for the evaluator.
        weight (float): How much this evaluator's result should be weighted in an aggregated result. Must be >= 0.
        threshold (float | None): The minimum score needed for this evaluation to be considered passing. Must be between 0 and 1 inclusive.
        config (dict[str, Any]): Arbitrary configuration options for the evaluator.
    """

    evaluator_id: str
    weight: float = Field(default=1, ge=0)
    threshold: float | None = Field(default=None, ge=0, le=1)
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

    # Evaluator ID is automatically set by evaluate
    evaluator_id: str = "MISSING EVALUATOR ID"
    passed: bool = False
    reasoning: str | LLMResponse | None = None
    normalised_score: float = 0
    execution_time: int = 0
    error: str | None = None


class EvaluationResponse(BaseModel):
    """
    Response object containing the aggregated evaluation results.

    Attributes:
        weighted_average_score (float): The sum of each normalised_score multiplied by its corresponding weight divided by the sum of all the weights.
        results (list[EvaluationResult]): List of results from each evaluator.
    """

    weighted_average_score: float | None = None
    results: list[EvaluationResult]
    is_partial: bool = False
    failure_count: int = 0


class JobCreatedResponse(BaseModel):
    """
    Response object returned by POST /evaluations.

    Attributes:
        task_id (UUID): The unique identifier of the enqueued Celery task. Used to poll for status.
        status (JobStatus): The current status of the task.
    """

    task_id: UUID
    status: JobStatus


class JobStatusResponse(BaseModel):
    """
    Response object returned by GET /evaluations/{task_id}.

    When status is COMPLETED, clients fetch the full result via GET /results/{result_id}.

    Attributes:
        task_id (UUID): The unique identifier of the Celery task.
        status (JobStatus): The current lifecycle state.
        result_id (UUID | None): The ID of the persisted AggregatedResultEntity, populated only when status is COMPLETED.
        error (str | None): Error message, populated only when status is FAILED.
    """

    task_id: UUID
    status: JobStatus
    result_id: UUID | None = None
    error: str | None = None

