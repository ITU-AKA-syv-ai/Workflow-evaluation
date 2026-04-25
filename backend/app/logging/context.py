from contextvars import ContextVar

evaluator_id_ctx: ContextVar[str | None] = ContextVar(
    "evaluator_id",
    default=None,
)

task_id_ctx: ContextVar[str | None] = ContextVar("task_id", default=None)
