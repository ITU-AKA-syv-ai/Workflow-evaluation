import datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator


class ResultQuery(BaseModel):
    """
    Filter, pagination, and sorting parameters used when retrieving stored results.

    Validates field-level constraints (e.g. score in [0, 1], limit in [1, 100]) and
    cross-field constraints (``start_date <= end_date``, ``min_score <= max_score``)
    at construction time, so consumers can rely on the values being well-formed.

    Used by both the ``GET /evaluations`` endpoint (parsed from query parameters)
    and the result repository (as a single argument to ``get_results``). Pydantic
    surfaces field-level violations as 422; the model validator below raises
    ``ValueError`` for cross-field violations, which Pydantic also turns into 422
    with a useful per-field error message.
    """

    model_config = {"extra": "forbid"}

    # Pagination
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=5, ge=1, le=100)

    # Filtering
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None
    min_score: float | None = Field(default=None, ge=0, le=1)
    max_score: float | None = Field(default=None, ge=0, le=1)
    evaluator_ids: list[str] | None = None
    tags: list[str] | None = None
    model_name: str | None = None
    model_version: str | None = None

    # Sorting
    sorting: Literal["date", "score"] = "date"
    sorting_direction: Literal["asc", "desc"] = "desc"

    @model_validator(mode="after")
    def _validate_ranges(self) -> Self:
        if self.start_date is not None and self.end_date is not None and self.start_date > self.end_date:
            raise ValueError("start_date cannot be after end_date")
        if self.min_score is not None and self.max_score is not None and self.min_score > self.max_score:
            raise ValueError("min_score cannot be greater than max_score")
        return self
