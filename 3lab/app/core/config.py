import os
import redislite # Import to allow patching of standard redis module
from pydantic_settings import BaseSettings

# For redislite, it often patches the standard redis library.
# So, we can use a standard-looking Redis URL, and redislite will handle it.
# The actual DB file path for redislite is often configured when redislite.Redis is instantiated or via env vars redislite might pick up.
# We defined DEFAULT_REDISLITE_DB_PATH which is used by tasks.py for direct Redis PubSub.
# For Celery, let's rely on redislite patching standard Redis URLs.

# Ensure redislite is imported somewhere before Celery app initialization, e.g. in celery_app.py or even tasks.py as it is now.

DEFAULT_REDISLITE_DB_NAME = "shared_lab3_data.db"
# Absolute path to the desired redislite DB file
# All components (Celery, FastAPI listener, Task publisher) will use this file.
DB_FILE_PATH = os.path.abspath(DEFAULT_REDISLITE_DB_NAME)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Lab 3 Bruteforce API"

    # Common URL for Celery broker, backend, and PubSub via redislite
    # The dbfilename GET parameter is used by redislite when patching from_url methods.
    COMMON_REDISLITE_URL: str = f"redis://localhost:6379/0?dbfilename={DB_FILE_PATH}"

    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", COMMON_REDISLITE_URL)
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", COMMON_REDISLITE_URL)
    
    # This can be used if a direct path is ever needed, but from_url with dbfilename is preferred.
    REDISLITE_DB_FILE_ABSPATH: str = DB_FILE_PATH 

settings = Settings()

print(f"--- Config Initialized ---")
print(f"Shared Redislite DB File (via URL parameter dbfilename): {DB_FILE_PATH}")
print(f"Common Redislite URL for all components: {settings.COMMON_REDISLITE_URL}")
print(f"Celery Broker URL: {settings.CELERY_BROKER_URL}")
print(f"--- End Config Initialized ---")
# No global redislite.config manipulation as it was incorrect.
# We rely on redislite's default patching behavior for standard Redis URLs
# and explicit path for direct redislite.StrictRedis instantiation. 