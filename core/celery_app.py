import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
app = Celery('user')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'disable_expired_staff': {
        'task': 'organizations.tasks.disable_expired_staff',
        'schedule': crontab(hour=0, minute=0),
    }
}
