from typing import Any

from pydantic import BaseModel, Field

from app.core.providers.base import LLMResponse


class EvaluatorInfo(BaseModel):
    """
    Information about an evaluator.
    Attributes:
        evaluator_id (str): Unique identifier for the evaluator.
        description (str): Description of what the evaluator checks.
        config_schema (dict[str, Any]): Arbitrary configuration options for the evaluator.
    """

    evaluator_id: str = Field(..., description="Unique identifier for the evaluator.", example="llm_judge")

    description: str = Field(
        ...,
        description="Description of what the evaluator checks.",
        example="Evaluates model output against a rubric using an LLM.",
    )
    config_schema: dict[str, Any] = Field(
        ...,
        description="Schema describing which configuration fields this evaluator accepts.",
        example={
                "type": "object",
                "properties": {
                    "rubric": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Criteria used to evaluate the model output.",
                    }
                },
                "required": ["rubric"],
            }
        ,
    )


class EvaluatorConfig(BaseModel):
    """
    Configuration for a single evaluator.

    Attributes:
        evaluator_id (str): Unique identifier for the evaluator.
        weight (float): How much this evaluator's result should be weighted in an aggregated result. Must be >= 0.
        threshold (float | None): The minimum score needed for this evaluation to be considered passing. Must be between 0 and 1 inclusive.
        config (dict[str, Any]): Arbitrary configuration options for the evaluator.
    """

    evaluator_id: str = Field(
        ...,  # Required
        description="Unique identifier for the evaluator. (e.g. 'rule_based_evaluator' or 'llm_judge')",
        example="llm_judge",
    )

    weight: float = Field(
        default=1,
        ge=0,
        description="Weight of this evaluator's result. Must be greater than or equal to 0.",
        example=0.5,
    )

    threshold: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Minimum score required for this evaluation to be considered passing.",
        example=0.8,
    )

    config: dict[str, Any] = Field(
        ...,  # Required
        description="""
        Evaluator-specific configuration.
        
        The structure depends on the evaluator_id.
        For example:
        - 'llm_judge' has a rubric with different criteria.
        - 'rule-based_evaluator' expects a list of rules.
        
        See /evaluators for the expected configuration schema for each evaluator.
        """,
        example={
            "prompt": "How can I improve my sleep quality?",
            "rubric": [
                "correctness: is the advice scientifically accurate?",
                "clarity: is the explanation easy to understand?",
                "completeness: does it cover key aspects of sleep hygiene?",
            ],
        },
    )


class EvaluationRequest(BaseModel):
    """
    Request object containing the output to evaluate and the evaluator configurations.

    Attributes:
        model_output (str): The text or content which has been produced by some model that is to be evaluated.
        configs (list[EvaluatorConfig]): List of evaluator configurations to use.
    """

    model_output: str = Field(
        ...,  # Required
        description="The text or content which has been produced by some model that is to be evaluated.",
        example="You can improve sleep quality by maintaining a consistent bedtime, avoiding screens before sleep, and keeping your room dark and cool.",
    )

    configs: list[EvaluatorConfig] = Field(
        ...,  # Required
        description="List of evaluator configurations to use with the model output.",
    )


class EvaluationResult(BaseModel):
    """
    Result of a single evaluator's evaluation.

    Attributes:
        evaluator_id (str): The ID of the evaluator that produced this result.
        passed (bool): Whether the output passed the evaluator's criteria.
        reasoning (str| LLMResponse | None): Explanation of why the evaluation passed or failed.
        normalised_score (float): Score given by the evaluator between 0 and 1.
        execution_time (int): Evaluator execution time measured in milliseconds.
        error (str | None): Error message if the evaluator failed.
    """

    # Evaluator ID is automatically set by evaluate
    evaluator_id: str = Field(
        default="MISSING EVALUATOR ID",
        description="The ID of the evaluator that produced this result.",
        example="llm_judge",
    )

    passed: bool = Field(
        default=False,
        description="Whether the output passed the evaluator's criteria.",
        example=True,
    )
    reasoning: str | LLMResponse | None = Field(
        default=None,
        description="Explanation of why the evaluation passed or failed. May be plain text or a structured LLM response.",
        example="The answer is clear and covers the main criteria in the rubric.",
    )

    normalised_score: float = Field(
        default=0,
        ge=0,
        le=1,
        description="Score given by the evaluator, normalised to a value between 0 and 1.",
        example=0.85,
    )

    execution_time: int = Field(
        default=0,
        ge=0,
        description="Time spent running this evaluator, measured in milliseconds.",
        example=124,
    )

    error: str | None = Field(
        default=None,
        description="Error message if the evaluator failed. Null if evaluation completed successfully.",
        example="Invalid config",
    )


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
