from app.core.evaluators.base import BaseEvaluator


class TestEvaluator2(BaseEvaluator):
    def __init__(self) -> None:
        super().__init__()  # ty:ignore[missing-argument]


class NotASubclass:
    pass
