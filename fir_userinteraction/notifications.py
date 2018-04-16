"""
Module leveraging fir_notifications in order to notify users regarding actions on their incidents
"""
from datetime import datetime

from django.core.mail import EmailMessage
from django.template import Context, Template
import logging

from fir_notifications.methods import NotificationMethod


def render_date_time_field(data_dict):
    date = data_dict.get('date')
    if date:
        date = date[:-1] if date.endswith('Z') else date
        data_dict['date'] = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S').strftime("%b %d %Y %H:%M:%S")
    return data_dict


class AutoNotifyMethod(NotificationMethod):
    use_subject = True
    use_description = True
    name = 'autonotify'
    verbose_name = 'Auto Notify'

    def __init__(self):
        super(AutoNotifyMethod, self).__init__()
        self.server_configured = True

    @staticmethod
    def send_email(data_dict, template, responsible, cc_recipients):
        c = Context(data_dict)

        subject_rendered = Template(template.subject).render(c)
        body_rendered = Template(template.body).render(c)
        logging.info('Sending mail to: {}, cc: {}'.format(responsible, cc_recipients))

        msg = EmailMessage(subject=subject_rendered, body=body_rendered,
                           from_email='noreply@cern.ch',
                           to=[responsible.email],
                           cc=cc_recipients)
        msg.content_subtype = 'html'
        msg.send()

    @staticmethod
    def get_rendered_answers(quiz):
        from fir_userinteraction.models import QuizAnswer
        answers = QuizAnswer.objects.filter(quiz_id=quiz.id)
        response = ''
        for answer in answers:
            response += '* ' + answer.question_group.title + '\n'
            response += answer.question.label + '\n\n'

        return response

    def populate_data_dict(self, comment, action, quiz, incident):
        """
        Build a context for populating the email template
        :param comment: the comment db item
        :param action: string denoting the action that took place
        :param quiz: the quiz db item
        :param incident: incident db entity
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
            data_dict = {
                'comment': comment.comment,
                'incident': incident
            }
        data_dict['username'] = quiz.user.username
        return data_dict

    def handle_incident_comment(self, instance):
        action = instance.action.name.lower()
        incident = instance.incident
        category_template = incident.category.categorytemplate_set.filter(type=action)

        if hasattr(incident, 'quiz') and len(category_template) > 0:
            category_template = category_template[0]
            quiz = incident.quiz
            watchlist = [item.email for item in quiz.quizwatchlistitem_set.all()]
            data_dict = self.populate_data_dict(instance, action, quiz, incident)

            self.send_email(data_dict, category_template, quiz.user, watchlist)

    def send(self, event, users, instance, paths):
        logging.info("Sending auto-notify message: {},{},{},{}".format(event, users, instance, paths))
        if event == 'incident:commented':
            self.handle_incident_comment(instance)

    def configured(self, user):
        return super(AutoNotifyMethod, self).configured(user) and user.email is not None
