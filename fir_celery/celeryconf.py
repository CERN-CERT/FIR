from __future__ import absolute_import, unicode_literals

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fir.settings')

from django.conf import settings


def get_redis_url():
    redis_password = ''
    if hasattr(settings, 'REDIS_PASS') and settings.REDIS_PASS:
        redis_password = ':{}@'.format(settings.REDIS_PASS)

    return 'redis://{}{}:{}/{}'.format(redis_password, settings.REDIS_HOST, settings.REDIS_PORT,
                                       settings.REDIS_DB)


celery_app = Celery(
    'celeryconf',
    broker=get_redis_url(),
    backend=get_redis_url()
)

celery_app.config_from_object(settings, namespace='CELERY')
celery_app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

if __name__ == '__main__':
    celery_app.start()
