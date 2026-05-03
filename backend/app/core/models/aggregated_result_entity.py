from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.models.evaluation_model import EvaluationRequest, EvaluationResponse


class AggregatedResultEntity(BaseModel):
    """
    Dataclass for aggregated results.
    Represents a persisted evaluation, combining:
    - The original request
    - The evaluated result
    - Optional database metadata.

    Used for internal storage and retrieval.

    Attributes:
        request (EvaluationRequest): The original evaluation request.
        result (EvaluationResult): The outcome of the evaluation.
        id (int, optional): The unique identifier of the evaluation. Defaults to None.
        created_at (datetime, optional): The timestamp when the evaluation was created. Defaults to None.
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

    created_at: datetime | None = Field(
        default=None, description="The timestamp when the evaluation was created.", example="2026-04-22 12:00:13.238855"
    )


class AggregatedResultResponse(BaseModel):
    """
    Response object returned by the /evaluate endpoint.

    Contains:
    - A reference id for use in the database.
    - The evaluation response.
    - Whether the response was persisted.

    Attributes:
        result_id(UUID | None): The id of the persisted entity to be used to get it in the future
        result(EvaluationResponse): The response for the evaluation
        persisted(bool): Boolean indicating if the result was persisted
    """

    result_id: UUID | None = Field(
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
