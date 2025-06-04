from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.celery.tasks"]  # Points to where task definitions are
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Optional: Configure Celery to use redislite more explicitly if needed,
    # though usually the broker/backend URL is sufficient.
    broker_transport_options={
        'visibility_timeout': 3600, # 1 hour, example
        # redislite specific options can be added here if any, consult redislite docs
    },
    result_backend_transport_options={},
)

if __name__ == "__main__":
    # This is for running the worker directly, e.g., python -m app.celery.celery_app worker -l info
    # The command to run celery worker will be: celery -A app.celery.celery_app worker -l info
    # Or, if main.py imports and uses celery_app, it might be relative to main.
    # For this structure, it's usually `celery -A main.celery_app worker -l INFO` if celery_app is exposed in main.py
    # Or `celery -A app.celery.celery_app worker -l INFO` if run from the `lab3` directory.
    pass 