import os
from .settings import *  # noqa


DEBUG = True
ALLOWED_HOSTS = ["*"]

# TASKS = {
#     "default": {
#         "BACKEND": "django.tasks.backends.immediate.ImmediateBackend",
#     }
# }

# CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
# CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "")
CELERY_TASK_ALWAYS_EAGER = False