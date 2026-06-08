from celery import Celery

celery_app = Celery(
    "nexora",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.update(

    task_serializer="json",

    accept_content=["json"],

    result_serializer="json",

    timezone="UTC",

    enable_utc=True,

    task_track_started=True,

    result_expires=3600,
)