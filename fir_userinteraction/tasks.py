from __future__ import absolute_import, unicode_literals

from datetime import datetime

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import Q

from fir_userinteraction.models import get_or_create_label
from incidents.models import Incident, Comments


def get_configured_max_time():
    threshold = 7
    if hasattr(settings, 'CELERY_RENOTIFICATION_THRESHOLD'):
        threshold = settings.CELERY_RENOTIFICATION_THRESHOLD
    return threshold


def check_incident_response_time(incident):
    max_threshold = get_configured_max_time()
    last_comment_time = incident.get_last_comment().date
    days_difference = abs(datetime.now() - last_comment_time).days - max_threshold
    if days_difference >= 0:
        return True
    return False


@shared_task
def check_for_renotification():
    """
    Celery task that looks through the database and renotifies users if they have been inactive for a period of time
    logn enough
    """
    logger = get_task_logger(__name__)
    incidents = Incident.objects.filter(Q(quiz__is_answered=False) & (Q(status='O') | Q(status='B')))
    incidents_to_renotify = list(filter(lambda i: check_incident_response_time(i), incidents))

    for incident in incidents_to_renotify:
        action = 'renotify{}'.format(incident.severity)
        category_templates = incident.category.categorytemplate_set.filter(type=action)
        if category_templates:
            Comments.objects.create(incident=incident,
                                    comment='Renotification of severity {}'.format(incident.severity),
                                    action=get_or_create_label(action.capitalize()),
                                    opened_by=incident.opened_by)
        else:
            logger.info('Unable to send renotify message, no template defined for: {}'.format(action))
    else:
        logger.info('Done with the renotifications')
