import uvicorn
from fastapi import FastAPI

from app.api.api import api_router # Import the main API router
from app.api.endpoints.bruteforce import startup_event, shutdown_event # Import lifecycle events
from app.core.config import settings
from app.celery.celery_app import celery_app # Import celery_app

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"/api/v1/openapi.json"
)

# Include lifecycle events for Redis Pub/Sub listener
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

# Include the API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

# Expose celery_app for worker (e.g., `celery -A main.celery_app worker -l INFO`)
# This line is mainly for discovery by Celery CLI if main.py is in PYTHONPATH.
# The actual celery_app instance is already imported.
# No specific code needed here other than the import if main is the entry point for celery.

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 