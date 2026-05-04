from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.workers.tasks import run_evaluation_task


@pytest.fixture()
def valid_request_dict() -> dict[str, Any]:
    return {
        "model_output": "idk",
        "configs": [{"evaluator_id": "mock_evaluator", "weight": 1.0, "config": {}}],
    }


@patch("app.workers.tasks.update_evaluation_result")
@patch("app.workers.tasks.get_orchestrator_for_worker")
def test_run_evaluation_happy_path(
    mock_get_orchestrator: MagicMock,
    mock_update_result: MagicMock,
    valid_request_dict: dict[str, Any],
) -> None:
    """On success the task persists the response. Lifecycle status is now Celery's job."""
    job_id = uuid4()
    fake_response = MagicMock()
    mock_get_orchestrator.return_value.evaluate = AsyncMock(return_value=fake_response)

    run_evaluation_task.apply(args=(job_id, valid_request_dict)).get()

    mock_update_result.assert_called_once_with(job_id, result=fake_response)


@patch("app.workers.tasks.update_evaluation_result")
@patch("app.workers.tasks.get_orchestrator_for_worker")
def test_run_evaluation_does_not_persist_on_error(
    mock_get_orchestrator: MagicMock,
    mock_update_result: MagicMock,
    valid_request_dict: dict[str, Any],
) -> None:
    """On failure the task must not call update_evaluation_result; the exception
    propagates so Celery records FAILURE in its result backend."""
    job_id = uuid4()
    mock_get_orchestrator.return_value.evaluate = AsyncMock(
        side_effect=Exception("this betta blow up or i will be mad")
    )

    with pytest.raises(Exception, match="this betta blow up or i will be mad"):
        run_evaluation_task.apply(args=(job_id, valid_request_dict)).get()

    mock_update_result.assert_not_called()


@patch("app.workers.tasks.update_evaluation_result")
@patch("app.workers.tasks.get_orchestrator_for_worker")
def test_run_evaluation_reraises(
    mock_get_orchestrator: MagicMock,
    _: MagicMock,
    valid_request_dict: dict[str, Any],
) -> None:
    job_id = uuid4()
    mock_get_orchestrator.return_value.evaluate = AsyncMock(side_effect=ValueError("specific error"))

    with pytest.raises(ValueError):
        run_evaluation_task.apply(args=(job_id, valid_request_dict)).get()
