from __future__ import absolute_import, unicode_literals

from datetime import datetime, timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from django.db.models import Q

from fir_userinteraction.models import get_or_create_label, get_or_create_global_category, AutoNotifyDuration
from incidents.models import Incident, Comments
from fir_userinteraction.helpers import get_django_setting_or_default


def get_configured_max_time(incident):
    days = get_django_setting_or_default('UI_DEFAULT_MAX_DAYS', 7)
    threshold = timedelta(days=days)
    global_category = get_or_create_global_category()
    auto_notify_durations = AutoNotifyDuration.objects.filter(category=incident.category,
                                                              severity=incident.severity)
    global_auto_notify_durations = AutoNotifyDuration.objects.filter(category=global_category,
                                                                     severity=incident.severity)
    if auto_notify_durations:
        threshold = auto_notify_durations[0].duration
    elif global_auto_notify_durations:
        threshold = global_auto_notify_durations[0].duration
    return threshold


def check_incident_response_time(incident):
    max_threshold = get_configured_max_time(incident)
    last_comment_time = incident.get_last_comment().date
    if abs(datetime.now() - last_comment_time) > max_threshold:
        return True
    return False


@shared_task
def check_for_renotification():
    """
    Celery task that looks through the database and renotifies users if they have been inactive for a period of time
    long enough
    """
    logger = get_task_logger(__name__)
    incidents = Incident.objects.filter(Q(status='B'))
    incidents_to_renotify = list(filter(lambda i: check_incident_response_time(i), incidents))
    global_category = get_or_create_global_category()
    for incident in incidents_to_renotify:
        action = 'renotify{}'.format(incident.severity)
        category_templates = incident.category.categorytemplate_set.filter(type=action)
        global_category_templates = global_category.categorytemplate_set.filter(type=action)
        if category_templates or global_category_templates:
            Comments.objects.create(incident=incident,
                                    comment='Renotification of severity {}'.format(incident.severity),
                                    action=get_or_create_label(action.capitalize()),
                                    opened_by=incident.opened_by)
        else:
            logger.warning('Unable to send renotify message, no template defined for: {}'.format(action))
    else:
        logger.info('Done with the renotifications')
