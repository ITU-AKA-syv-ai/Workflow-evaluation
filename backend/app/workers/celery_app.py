from celery import Celery

from app.config.settings import get_settings

settings = get_settings()

# Redis is used as the broker (queue). The result backend is the application's Postgres
# database, so task status and results are durable and queryable alongside existing
# application data. Celery creates its own celery_taskmeta table on first write.
# NOTE: Adjust settings.redis.url to match the actual path used in your settings module.
celery_app = Celery(
    "evaluation_workers",
    broker=settings.redis.url,
    backend=f"db+{settings.db.sqlalchemy_database_uri}",
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    # Report STARTED state so GET can distinguish pending from running tasks.
    # Without this, Celery skips STARTED for performance and tasks appear to go directly
    # from PENDING to SUCCESS/FAILURE.
    task_track_started=True,
    # Soft time limit raises an exception inside the task so the failure is recorded.
    # Hard time limit kills the worker if the soft limit is ignored. Hard must be greater than soft.
    task_soft_time_limit=300,
    task_time_limit=330,
    # JSON serialization only. Pickle can execute arbitrary code from the broker.
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
