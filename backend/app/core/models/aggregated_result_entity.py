from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

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

    request: EvaluationRequest
    result: EvaluationResponse | None
    id: UUID | None = None
    status: EvaluationStatus | None = None
    created_at: datetime | None = None
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

    job_id: UUID | None
    result: EvaluationResponse
    persisted: bool
