import os

env = os.environ.get('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *
else:
    from .development import *


# from ..celery import app as celery_app

# __all__ = ('celery_app',)