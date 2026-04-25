from celery import Celery

from app.config.settings import get_settings

"""
Method used to return a celery_app. Mainly used to enable mocking in testing, so we can import the file without loading the settings.
"""


def create_celery() -> Celery:

    settings = get_settings()

    # Redis is used as the broker (queue). We do not use celeries built-in result backend to prevent celery from making its own metadata.
    # The result backend is the application's Postgres

    if not settings.redis.host or settings.redis.host == "localhost":
        # If this triggers in Docker, your .env isn't being read!
        print(f"WARNING: Host is {settings.redis.host}. Redis might not be found in Docker.")

    celery_app = Celery(
        "evaluation_workers",
        broker=settings.redis.url,
    )

    celery_app.autodiscover_tasks(["app.workers.tasks"])

    celery_app.conf.update(
        # Soft time limit raises an exception inside the task so the failure is recorded.
        task_soft_time_limit=300,
        # Hard time limit kills the worker if the soft limit is ignored. Hard must be greater than soft.
        task_time_limit=330,
        timezone="UTC",
        enable_utc=True,
    )

    return celery_app


celery_app = create_celery()
