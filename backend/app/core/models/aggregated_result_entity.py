from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from backend.app.core.models.evaluation_model import EvaluationRequest, EvaluationResponse


class AggregatedResultEntity(BaseModel):
    """
    Dataclass for aggregated results.
    Represents an evaluation stored as a combination of the request and the result, optionally including database metadata.

    Attributes:
        request (EvaluationRequest): The original evaluation request.
        result (EvaluationResult): The outcome of the evaluation.
        id (int, optional): The unique identifier of the evaluation. Defaults to None.
        created_at (datetime, optional): The timestamp when the evaluation was created. Defaults to None.
    """

    request: EvaluationRequest
    result: EvaluationResponse
    id: UUID | None = None
    created_at: datetime | None = None


class AggregatedResultResponse(BaseModel):
    """
    Return object for /evaluate which contains an id if the response was persisted, a bool indicating if it was persisted and then the actual response

    Attributes:
        result_id(UUID | None): The id of the persisted entity to be used to get it in the future
        result(EvaluationResponse): The response for the evaluation
        persisted(bool): Boolean indicating if the result was peristed
    """

    result_id: UUID | None
    result: EvaluationResponse
    persisted: bool
