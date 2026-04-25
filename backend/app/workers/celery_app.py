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
    )

    app.autodiscover_tasks(["app.workers.tasks"])

    app.conf.update(
        # Soft time limit raises an exception inside the task so the failure is recorded.
        task_soft_time_limit=300,
        # Hard time limit kills the worker if the soft limit is ignored. Hard must be greater than soft.
        task_time_limit=330,
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
