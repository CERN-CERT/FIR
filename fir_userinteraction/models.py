from __future__ import unicode_literals

import uuid

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.shortcuts import get_object_or_404

from incidents.models import Incident, IncidentCategory, Comments, Label

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


class CommentAttachment(models.Model):
    """
    Sometimes you may need to attach an extra piece of data to a comment in order to create a notification email
    """
    comment = models.OneToOneField(Comments, on_delete=models.CASCADE)
    attachment = models.TextField()

    def __str__(self):
        return '{} | attachment: {}'.format(self.comment, self.attachment)


## Helper methods

def get_or_create_label(name, group='action'):
    from incidents.models import LabelGroup
    group = LabelGroup.objects.get(name=group)
    try:
        label = Label.objects.get(name=name, group=group)
    except Label.DoesNotExist:
        label = Label.objects.create(name=name, group=group)
    return label


def get_incident_for_user(authorization_target, incident_id, request):
    if authorization_target is None:
        incident = get_object_or_404(
            Incident.authorization.for_user(request.user, 'incidents.view_incidents'),
            pk=incident_id)
    else:
        incident = authorization_target
    return incident


def get_or_create_quiz(request, incident):
    try:
        user_quiz = Quiz.objects.get(incident_id=incident.id)
    except Quiz.DoesNotExist:
        template = get_object_or_404(QuizTemplate, category=incident.category)
        user_quiz = Quiz.objects.create(template=template, incident=incident, user=request.user)
    return user_quiz


# @notification_event('quiz:updated', post_save, Quiz, verbose_name='Quiz updated',
#                     section='Quiz updated')
# def incident_created(sender, instance, **kwargs):
#     return instance, instance.incident.concerned_business_lines
