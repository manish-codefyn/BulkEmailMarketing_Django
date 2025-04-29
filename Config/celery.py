
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Config.settings.development')


app = Celery('Config')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related config keys should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Configure logging
logger = logging.getLogger('celery')
logger.setLevel(logging.DEBUG)
