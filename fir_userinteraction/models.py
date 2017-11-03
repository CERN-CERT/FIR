from __future__ import unicode_literals

from django.contrib.auth import get_user_model

from incidents.models import Incident, IncidentCategory
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
    required = models.BooleanField(default=True)
    label = models.CharField(max_length=100)

    def __str__(self):
        return self.label


class QuizTemplate(models.Model):
    category = models.OneToOneField(IncidentCategory, on_delete=models.CASCADE)
    questions = models.ManyToManyField(Question, verbose_name='list of quiz questions')
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


class QuizGroup(models.Model):
    title = models.CharField(max_length=100)


class QuizAnswer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    answer_value = models.CharField(max_length=100)

    def __str__(self):
        return 'Answer to question "{}" in quiz {}'.format(self.question.label, self.quiz.id)
