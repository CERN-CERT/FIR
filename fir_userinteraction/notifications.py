"""
Module leveraging fir_notifications in order to notify users regarding actions on their incidents
"""
from datetime import datetime

from django.core.mail import EmailMessage
from django.template import Context, Template
from fir_userinteraction.constants import USERS_BL, GROUPS_BL
from certsoclib.params import LDAP_USER_SEARCH, LDAP_GROUP_SEARCH
from certsoclib.ldap_connector import LdapConnector
import logging

from fir_notifications.methods import NotificationMethod


def render_date_time_field(data_dict):
    date = data_dict.get('date')
    if date:
        date = date[:-1] if date.endswith('Z') else date
        data_dict['date'] = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S').strftime("%b %d %Y %H:%M:%S")
    return data_dict


def get_base_business_line(bl):
    result_bl = bl
    while result_bl.get_parent() is not None:
        result_bl = result_bl.get_parent()
    return result_bl


def get_query_type_from_base_bl(bl):
    base_bl = get_base_business_line(bl)
    if base_bl.name == USERS_BL:
        return LDAP_USER_SEARCH
    elif base_bl.name == GROUPS_BL:
        return LDAP_GROUP_SEARCH


def get_user_from_ldap(user):
    con = LdapConnector()
    ldap_result = filter(lambda x: x.cn == user.username,
                         con.search_in_ldap(user.username, query_type=LDAP_USER_SEARCH))
    if ldap_result:
        return ldap_result[0]
    return user.mail


def get_bl_mails_from_ldap(bls):
    con = LdapConnector()
    results = []
    for bl in bls:
        ldap_result = filter(lambda x: x.cn == bl.name,
                             con.search_in_ldap(bl.name, query_type=get_query_type_from_base_bl(bl)))
        if ldap_result:
            results.append(ldap_result[0].mail)
    return results


class AutoNotifyMethod(NotificationMethod):
    use_subject = True
    use_description = True
    name = 'autonotify'
    verbose_name = 'Auto Notify'

    def __init__(self):
        super(AutoNotifyMethod, self).__init__()
        self.server_configured = True

    @staticmethod
    def send_email(data_dict, template, responsible_mail, cc_recipients):
        from django.conf import settings
        c = Context(data_dict)
        sender_email = 'noreply@cern.ch'
        if hasattr(settings, 'EMAIL_FROM') and settings.EMAIL_FROM:
            sender_email = settings.EMAIL_FROM

        subject_rendered = Template(template.subject).render(c)
        body_rendered = Template(template.body).render(c)
        logging.info('Sending mail to: {}, cc: {}'.format(responsible_mail, cc_recipients))

        msg = EmailMessage(subject=subject_rendered, body=body_rendered,
                           from_email=sender_email,
                           to=[responsible_mail],
                           cc=cc_recipients)
        msg.content_subtype = 'html'
        response = msg.send()
        logging.info('Sent a number of {} emails'.format(response))

    @staticmethod
    def get_rendered_answers(quiz):
        from fir_userinteraction.models import QuizAnswer
        answers = QuizAnswer.objects.filter(quiz_id=quiz.id)
        response = ''
        for answer in answers:
            response += '* ' + answer.question_group.title + '\n'
            response += answer.question.label + '\n\n'

        return response

    @staticmethod
    def get_category_templates(incident, action):
        """
        Get the category templates for an incident's category and the last action. If none are found
        then return the global category templates (if they exist). Otherwise, an empty list is returned
        :param incident: incident model from the db
        :param action: name of the last action
        :return:
        """
        from fir_userinteraction.models import get_or_create_global_category

        global_category = get_or_create_global_category()
        category_templates = incident.category.categorytemplate_set.filter(type=action)
        global_category_templates = global_category.categorytemplate_set.filter(type=action)
        if category_templates:
            return category_templates
        elif global_category_templates:
            return global_category_templates
        return []

    @staticmethod
    def build_unauthorized_incident_url(user_account_enabled, quiz, data_dict):
        """
        If the user is disabled, the incident URL has to be changed
        :param user_account_enabled: boolean representing user state
        :param quiz: the quiz assigned to the user
        :param data_dict: the dictionary with which to populate the data
        :return: the updated dictionary
        """
        if not user_account_enabled and 'incident_url' in data_dict:
            unauthenticated_url = ('/'.join(data_dict['incident_url'].split('/')[:3]) +
                                   '/' + '/'.join(['form', str(quiz.id)]))
            data_dict['incident_url'] = unauthenticated_url

        return data_dict

    def populate_data_dict(self, comment, action, quiz, incident, user_account_enabled):
        """
        Build a context for populating the email template
        :param comment: the comment db item
        :param action: string denoting the action that took place
        :param quiz: the quiz db item
        :param incident: incident db entity
        :param user_account_enabled: boolean telling if the user is enabled or not
        :return: dict of str
        """
        from fir_userinteraction.models import get_artifacts_for_incident

        data_dict = {}
        if action == 'user answered':
            rendered_answers = self.get_rendered_answers(quiz)
            data_dict.update({
                'quiz': rendered_answers,
                'date': comment.date.strftime("%b %d %Y %H:%M:%S"),
                'incident_name': incident.subject,
                'incident_desc': incident.description
            })
        elif action == 'initial':
            data_dict.update(get_artifacts_for_incident(incident))
            data_dict = render_date_time_field(data_dict)
        else:
            data_dict.update(get_artifacts_for_incident(incident))
            data_dict.update({
                'comment': comment.comment,
                'incident': incident
            })
        data_dict['username'] = quiz.user.username
        data_dict = self.build_unauthorized_incident_url(user_account_enabled, quiz, data_dict)
        return data_dict

    @staticmethod
    def populate_watchlist_from_ldap(quiz):
        watchlist_bls = [wl.business_line for wl in quiz.quizwatchlistitem_set.all()]
        return get_bl_mails_from_ldap(watchlist_bls)

    def handle_incident_comment(self, instance):
        action = instance.action.name.lower()
        incident = instance.incident
        category_templates = self.get_category_templates(incident, action)

        if hasattr(incident, 'quiz') and len(category_templates) > 0:
            category_template = category_templates[0]
            quiz = incident.quiz
            watchlist = self.populate_watchlist_from_ldap(quiz)
            user = get_user_from_ldap(quiz.user)
            data_dict = self.populate_data_dict(instance, action, quiz, incident, user.account_enabled())

            self.send_email(data_dict, category_template, user.mail, watchlist)

    def send(self, event, users, instance, paths):
        logging.info("Sending auto-notify message: {},{},{},{}".format(event, users, instance, paths))
        if event == 'incident:commented':
            self.handle_incident_comment(instance)

    def configured(self, user):
        return super(AutoNotifyMethod, self).configured(user) and user.email is not None
