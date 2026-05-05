from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.models.evaluation_model import EvaluationRequest, EvaluationResponse
from app.models import EvaluationStatus


class AggregatedResultEntity(BaseModel):
    """
    Dataclass for aggregated results. Represents an evaluation stored as a combination
    of the request and the response, optionally including database metadata.

    ``status`` is *not* persisted; it is populated at the API boundary from Celery's
    result backend (see ``job_status_service.get_job_state``). It's optional here so
    repositories can return entities without having to know about Celery.

    Attributes:
        request (EvaluationRequest): The original evaluation request.
        result (EvaluationResult): The outcome of the evaluation.
        id (int, optional): The unique identifier of the evaluation. Defaults to None.
        created_at (datetime, optional): The timestamp when the evaluation was created. Defaults to None.
        updated_at datetime | None = None: The timestamp when the evaluation was last updated. Defaults to None.
    """

    request: EvaluationRequest = Field(
        ...,  # Required
        description="The original evaluation request that produced this result.",
    )

    result: EvaluationResponse = Field(
        ...,  # Required
        description="The outcome of the evaluated request.",
        example={
            "weighted_average_score": 1,
            "results": [
                {
                    "evaluator_id": "rule_based_evaluator",
                    "passed": True,
                    "reasoning": "1/1 rules passed. format: pass (Output length 5 is within max length 10.)",
                    "normalised_score": 1,
                    "execution_time": 0,
                    "error": None,
                }
            ],
            "is_partial": False,
            "failure_count": 0,
        },
    )

    id: UUID | None = Field(
        default=None,
        description="The unique identifier of the stored evaluation.",
        example="124d925b-f2af-4691-888b-db9a8f0531f2",
    )

    status: EvaluationStatus | None = None

    created_at: datetime | None = Field(
        default=None, description="The timestamp when the evaluation was created.", example="2026-04-22 12:00:13.238855"
    )

    updated_at: datetime | None = None


class AggregatedResultResponse(BaseModel):
    """
    Return object for /evaluations which contains an id if the response was persisted, a bool
    indicating if it was persisted and then the actual response.

    Attributes:
        job_id (UUID | None): The id of the persisted entity to be used to fetch it later.
        result (EvaluationResponse): The evaluator response.
        persisted (bool): Whether the result was persisted.
    """

    job_id: UUID | None = Field(
        description="The unique identifier of the stored evaluation.", example="124d925b-f2af-4691-888b-db9a8f0531f2"
    )

    result: EvaluationResponse = Field(
        ...,  # Required
        description="The outcome of the evaluated request.",
        example={
            "weighted_average_score": 0.6666666666666666,
            "results": [
                {
                    "evaluator_id": "llm_judge",
                    "passed": False,
                    "reasoning": {
                        "results": [
                            {
                                "criterion_name": "correctness: is the advice scientifically accurate?",
                                "reasoning": "The advice to maintain a consistent bedtime, avoid screens ...",
                                "score": 4,
                            },
                            {
                                "criterion_name": "clarity: is the explanation easy to understand?",
                                "reasoning": "The statements are concise and easy to understand. They clearly ...",
                                "score": 3,
                            },
                            {
                                "criterion_name": "completeness: does it cover key aspects of sleep hygiene?",
                                "reasoning": "The advice covers several important elements but does not ...",
                                "score": 2,
                            },
                        ]
                    },
                    "normalised_score": 0.6666666666666666,
                    "execution_time": 8194,
                    "error": None,
                }
            ],
            "is_partial": False,
            "failure_count": 0,
        },
    )

    persisted: bool = Field(
        ...,  # Required
        description="Indicates whether the result was successfully stored in the database.",
        example=False,
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "result_id": "d55bc71f-4201-44be-be84-824c8187eb8c",
                "result": {
                    "weighted_average_score": 0.6666666666666666,
                    "results": [
                        {
                            "evaluator_id": "llm_judge",
                            "passed": False,
                            "reasoning": {
                                "results": [
                                    {
                                        "criterion_name": "correctness: is the advice scientifically accurate?",
                                        "reasoning": "The advice to maintain a consistent bedtime, avoid screens ...",
                                        "score": 4,
                                    },
                                    {
                                        "criterion_name": "clarity: is the explanation easy to understand?",
                                        "reasoning": "The statements are concise and easy to understand. They clearly ...",
                                        "score": 3,
                                    },
                                    {
                                        "criterion_name": "completeness: does it cover key aspects of sleep hygiene?",
                                        "reasoning": "The advice covers several important elements but does not ...",
                                        "score": 2,
                                    },
                                ]
                            },
                            "normalised_score": 0.6666666666666666,
                            "execution_time": 8194,
                            "error": None,
                        }
                    ],
                    "is_partial": False,
                    "failure_count": 0,
                },
                "persisted": True,
            }
        }
    )
