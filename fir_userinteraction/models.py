from __future__ import unicode_literals

from django.core.mail import EmailMessage
from django.core.validators import MinValueValidator, MaxValueValidator
from django.dispatch import Signal, receiver
from django.template import Context, Template
from ipware.ip import get_ip
from incidents.models import Incident, IncidentCategory, Comments, Label
from django.db import models
from django.contrib.auth.models import User
import uuid
from datetime import datetime

QUESTION_FIELD_TYPES = (
    ('django.forms.CharField', 'Char'),
    ('django.forms.BooleanField', 'Bool')
)

QUESTION_WIDGET_TYPES = (
    ('django.forms.Textarea', 'Text Area'),
    ('django.forms.CheckboxInput', 'Check Box')
)


# Create your models here.
class Question(models.Model):
    field_type = models.CharField(choices=QUESTION_FIELD_TYPES, max_length=100)
    widget_type = models.CharField(choices=QUESTION_WIDGET_TYPES, null=True, max_length=100)
    label = models.TextField()
    title = models.CharField(max_length=500)

    def __str__(self):
        return "{} ({})".format(self.title, self.widget_type)


class QuizGroupQuestionOrder(models.Model):
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    question_group = models.ForeignKey('QuestionGroup', on_delete=models.CASCADE)
    order_index = models.IntegerField(validators=[
        MaxValueValidator(100),
        MinValueValidator(1)
    ])

    def __str__(self):
        return '{} - [QG: {}] - [{}]'.format(self.order_index, self.question_group.title, self.question)

    class Meta:
        ordering = ['-order_index']


class QuizTemplateQuestionGroupOrder(models.Model):
    quiz_template = models.ForeignKey('QuizTemplate', on_delete=models.CASCADE)
    question_group = models.ForeignKey('QuestionGroup', on_delete=models.CASCADE)
    order_index = models.IntegerField(validators=[
        MaxValueValidator(100),
        MinValueValidator(1)
    ])

    def __str__(self):
        return '{} - [Quiz Template: {}] - [{}]'.format(self.order_index, self.quiz_template, self.question_group.title)

    class Meta:
        ordering = ['-order_index']


class QuestionGroup(models.Model):
    required = models.BooleanField(default=True)
    questions = models.ManyToManyField(Question, through='QuizGroupQuestionOrder',
                                       verbose_name='list of questions in this group')
    title = models.CharField(max_length=500)
    description = models.TextField(null=True)

    def __str__(self):
        return '{} | required: {}'.format(self.title, self.required)


class QuizTemplate(models.Model):
    category = models.OneToOneField(IncidentCategory, on_delete=models.CASCADE)
    question_groups = models.ManyToManyField(QuestionGroup, through='QuizTemplateQuestionGroupOrder',
                                             verbose_name='list of quiz groups')
    name = models.CharField(max_length=100, help_text='Name of this specific quiz template')
    useful_links = models.ManyToManyField('QuizTemplateUsefulLink', through='UsefulLinkOrdering',
                                          verbose_name='list of useful links for template')
    description = models.TextField(null=False)

    @property
    def sorted_template_links(self):
        return [x.template_useful_link for x in self.usefullinkordering_set.order_by('order_index')]

    def __str__(self):
        return self.name


class Quiz(models.Model):
    template = models.ForeignKey(QuizTemplate)
    incident = models.OneToOneField(Incident, on_delete=models.CASCADE)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    answers = models.ManyToManyField(Question, through='QuizAnswer')
    is_answered = models.BooleanField(default=False)
    user = models.ForeignKey(User, null=True)

    class Meta:
        verbose_name_plural = 'quizzes'

    def __str__(self):
        return '{} - Quiz for incident {}'.format(self.id, self.incident.id)


class QuizAnswer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    question_group = models.ForeignKey(QuestionGroup, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    answer_value = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return '{} - Question: "{}"'.format(self.question.label, self.quiz.id)


# Watchlist for any action performed
class QuizWatchListItem(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    email = models.CharField(max_length=100, help_text='Email address for the watchlist')

    def __str__(self):
        return '{} - Quiz: "{}", incident: {}'.format(self.email, self.quiz.id, self.quiz.incident.id)


class QuizTemplateUsefulLink(models.Model):
    label = models.CharField(max_length=100, help_text='Label for identifying the help list item')
    text = models.TextField()

    def __str__(self):
        return 'id={} | {}'.format(self.id, self.label)


class UsefulLinkOrdering(models.Model):
    template_useful_link = models.ForeignKey(QuizTemplateUsefulLink, on_delete=models.CASCADE)
    quiz_template = models.ForeignKey(QuizTemplate, on_delete=models.CASCADE)
    order_index = models.IntegerField(validators=[
        MaxValueValidator(100),
        MinValueValidator(1)
    ])

    def __str__(self):
        return 'link={} | quiz_template={}'.format(self.template_useful_link, self.quiz_template)

    class Meta:
        ordering = ['-order_index']


# Signals
model_updated = Signal(providing_args=['instance', 'request'])
watchlist_updated = Signal(providing_args=['instance', 'extra_data'])


def build_userinteraction_path(request, incident_id):
    from django.conf import settings
    incident_suffix = '/incidents/{}'.format(incident_id)
    if settings.USER_INTERACTION_SERVER:
        return settings.USER_INTERACTION_SERVER + incident_suffix
    else:
        return '/'.join(request.build_absolute_uri().split('/', 4)[:3]) + incident_suffix


def get_or_create_user_answered_label():
    from incidents.models import LabelGroup
    group = LabelGroup.objects.get(name='action')
    try:
        label = Label.objects.get(name='User Answered', group=group)
    except Label.DoesNotExist:
        label = Label.objects.create(name='User Answered', group=group)
    return label


@receiver(model_updated, sender=Quiz)
def create_comment_for_answered_quiz(sender, instance, request, **kwargs):
    user = request.user if request.user is not None else 'AnonymousUser'
    ip = get_ip(request)

    quiz_url = build_userinteraction_path(request, instance.incident_id)
    full_user = '{}@{}'.format(str(user), str(ip))

    comment = Comments.objects.create(incident=instance.incident,
                                      comment='An incident form has been filled in: {}.\n The user that commented is: {}'.format(
                                          quiz_url,
                                          full_user),
                                      action=get_or_create_user_answered_label(),
                                      opened_by=instance.incident.opened_by)
    inc = instance.incident
    inc.status = 'O'
    inc.save()
    notify_watchers(instance, inc, instance.quizwatchlistitem_set.all(), 'answered')


@receiver(watchlist_updated, sender=Quiz)
def send_initial_notification_to_watchlist(sender, instance, extra_data, **kwargs):
    print('Creating initial watchlist notification...')
    watchlist_items = instance.quizwatchlistitem_set.all()
    notify_watchers(instance, instance.incident, watchlist_items, 'initial', extra_data=extra_data)


def notify_watchers(quiz, incident, watchlist, action_type, extra_data={}):
    cc_recipients = [item.email for item in watchlist]
    last_comment = incident.get_last_comment()
    responsible_email = incident.quiz.user.email
    category_templates = incident.category.categorytemplate_set.filter(type=action_type)
    last_action = last_comment.action.name
    if len(category_templates) > 0:
        cat_template = category_templates[0]

        if last_action == 'User Answered':
            answers_str = get_rendered_answers(quiz)
            c = Context(dict({
                'quiz': answers_str,
                'date': last_comment.date.strftime("%b %d %Y %H:%M:%S"),
                'incident_name': incident.subject,
                'incident_desc': incident.description
            }, **extra_data))

            subject_rendered = Template(cat_template.subject).render(c)
            body_rendered = Template(cat_template.body).render(c)
            inc = quiz.incident
            inc.status = 'O'
            inc.save()

            msg = EmailMessage(subject=subject_rendered, body=body_rendered,
                               from_email='noreply@cern.ch',
                               to=[responsible_email],
                               cc=cc_recipients)
            msg.content_subtype = 'html'
            msg.send()
        elif last_action == 'Alerting':
            pass
        else:
            date = extra_data.get('date')
            if date:
                date = date[:-1] if date.endswith('Z') else date
                extra_data['date'] = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S').strftime("%b %d %Y %H:%M:%S")
            c = Context(extra_data)
            subject_rendered = Template(cat_template.subject).render(c)
            body_rendered = Template(cat_template.body).render(c)

            msg = EmailMessage(subject=subject_rendered, body=body_rendered,
                               from_email='noreply@cern.ch',
                               to=[responsible_email],
                               cc=cc_recipients)

            msg.content_subtype = "html"
            msg.send()
    else:
        print('Nothing to do...')


def get_rendered_answers(quiz):
    answers = QuizAnswer.objects.filter(quiz_id=quiz.id)
    response = ''
    for answer in answers:
        response += '* ' + answer.question_group.title + '\n'
        response += answer.question.label + '\n\n'

    return response
