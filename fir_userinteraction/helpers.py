from importlib import import_module

from django.conf import settings
from django.core.mail import EmailMessage


def get_django_setting_or_default(setting_name, default):
    """
    Wrapper for checking if something exists in the settings or not. Return the default otherwise
    :param setting_name: the key of the config value
    :param default: the default value to get otherwise
    :return: whatever datatype you hoped to get from the settings
    """
    if hasattr(settings, setting_name) and getattr(settings, setting_name):
        return getattr(settings, setting_name)
    else:
        return default


def import_from_module(full_name):
    """
    Gets a module string and imports the function or class from it
    :param full_name: the dot-separated full path of the module
    :return: the class or object in the module
    """
    class_name = full_name.split('.')[-1]
    module_name = '.'.join(full_name.split('.')[:-1])
    return getattr(import_module(module_name), class_name)


def build_userinteraction_path(request, incident_id):
    """
    Takes the current request and incident id and creates the full url to the incident
    :param request: the current django request
    :param incident_id: the id of the incident
    :return: a proper url for the incident
    """
    incident_suffix = '/incidents/{}'.format(incident_id)
    ui_server = get_django_setting_or_default('USER_INTERACTION_SERVER', '')
    if ui_server:
        return ui_server + incident_suffix
    else:
        return '/'.join(request.build_absolute_uri().split('/', 4)[:3]) + incident_suffix


def send_admin_mails(subject, body, sender_email, as_html=True):
    """
    Send an email to all registered admins
    @param subject: the subject
    @param body: the body of the email, plaintext or HTML
    @param sender_email: the email that does all the sending
    @param as_html: whether to send the content as html or not
    """
    # Send
    admins = get_django_setting_or_default('ADMINS', None)
    if not admins:
        return
    mail = EmailMessage(
        subject='%s%s' % (settings.EMAIL_SUBJECT_PREFIX, subject), body=body,
        from_email=sender_email, to=[a[1] for a in admins],
    )
    if as_html:
        mail.content_subtype = 'html'
    mail.send()
