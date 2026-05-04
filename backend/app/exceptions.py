from uuid import UUID


class EvaluationError(Exception):
    """Base for all domain errors in the evaluation system."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        self.message = message


class NoEvaluatorsSpecifiedError(EvaluationError):
    def __init__(self) -> None:
        super().__init__("No evaluators specified in request")


class UnknownEvaluatorsError(EvaluationError):
    def __init__(self, names: list[str]) -> None:
        super().__init__(f"Unknown evaluators: {', '.join(names)}")


class ResultNotFoundError(EvaluationError):
    """Raised when a result with the given id does not exist."""

    status_code = 404

    def __init__(self, result_id: UUID) -> None:
        super().__init__(f"Result {result_id} not found")


class ResultPersistenceError(EvaluationError):
    """Raised when a result row could not be inserted/persisted."""

    status_code = 503

    def __init__(self, message: str = "Unable to accept your request. Please try again shortly.") -> None:
        super().__init__(message)


class EvaluationTaskQueueError(EvaluationError):
    """Raised when an evaluation task could not be enqueued onto the worker."""

    status_code = 503

    def __init__(self, message: str = "Unable to queue your request. Please try again shortly.") -> None:
        super().__init__(message)
