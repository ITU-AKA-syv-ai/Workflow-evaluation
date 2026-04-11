from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.models.evaluation_model import EvaluationRequest, EvaluationResponse


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
    result_id: UUID | None
    result: EvaluationResponse
    persisted: bool
