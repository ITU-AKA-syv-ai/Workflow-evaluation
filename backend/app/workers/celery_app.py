from functools import cache

from celery import Celery

from app.config.settings import get_settings


def _create_celery() -> Celery:
    settings = get_settings()

    if not settings.redis.host or settings.redis.host == "localhost":
        # If this triggers in Docker, your .env isn't being read!
        print(f"WARNING: Host is {settings.redis.host}. Redis might not be found in Docker.")

    app = Celery(
        "evaluation_workers",
        broker=settings.redis.url,
         backend=settings.db.celery_backend_uri,
    )

    app.autodiscover_tasks(["app.workers.tasks"])

    app.conf.update(
        # Soft time limit raises an exception inside the task so the failure is recorded.
        task_soft_time_limit=300,
        # Hard time limit kills the worker if the soft limit is ignored. Hard must be greater than soft.
        task_time_limit=330,
        # Without this, tasks go straight from PENDING -> SUCCESS/FAILURE in the backend.
        # With it on, workers report STARTED when they pick up a task, which makes the
        # RUNNING-equivalent observable from AsyncResult.state.
        task_track_started=True,
        # Persist the exception type, message, and traceback when a task fails so the
        # API can surface the reason without a custom error column.
        result_extended=True,
        timezone="UTC",
        enable_utc=True,
    )

    return app


@cache
def get_celery_app() -> Celery:
    """
    Return the singleton Celery app, creating it on first access.

    Lazy by design: settings aren't loaded until something actually asks
    for the app, so this module can be imported without valid Redis
    settings in the environment (useful for tests and CI).
    """
    return _create_celery()


# Module-level alias so the Celery CLI can discover the app.
# `celery -A app.workers.celery_app worker` imports this module and looks
# for an attribute named `app` (or `celery`) that's a Celery instance.
# Without this line, the worker fails to start with:
#   "Module 'app.workers.celery_app' has no attribute 'celery'"
app = get_celery_app()
