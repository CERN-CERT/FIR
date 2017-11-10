from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.dispatch import Signal, receiver
from ipware.ip import get_ip
from incidents.models import Incident, IncidentCategory, Comments, Label
from django.db import models
from django.contrib.auth.models import User
import uuid

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
    label = models.CharField(max_length=500)

    def __str__(self):
        return self.label


class QuestionGroup(models.Model):
    required = models.BooleanField(default=True)
    questions = models.ManyToManyField(Question, verbose_name='list of questions in this group')
    title = models.CharField(max_length=500)

    def __str__(self):
        return '{} | required: {}'.format(self.title, self.required)


class QuizTemplate(models.Model):
    category = models.OneToOneField(IncidentCategory, on_delete=models.CASCADE)
    question_groups = models.ManyToManyField(QuestionGroup, verbose_name='list of quiz groups')
    name = models.CharField(max_length=100, help_text='Name of this specific quiz template')

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


# Signals
model_updated = Signal(providing_args=['instance', 'request'])


@receiver(model_updated, sender=Quiz)
def create_comment_for_answered_quiz(sender, instance, request, **kwargs):
    user = request.user if request.user is not None else 'AnonymousUser'
    ip = get_ip(request)
    quiz_url = request.build_absolute_uri()
    full_user = '{}@{}'.format(str(user), str(ip))

    Comments.objects.create(incident=instance.incident,
                            comment='An incident form has been filled in: {}.\n The user that commented is: {}'.format(
                                quiz_url,
                                full_user),
                            action=Label.objects.get(name='Alerting', group__name='action'),
                            opened_by=instance.incident.opened_by)
