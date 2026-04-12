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
