from __future__ import unicode_literals

import uuid

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.shortcuts import get_object_or_404
from ipware.ip import get_ip

from fir_userinteraction.constants import GLOBAL_CATEGORY_NAME, QUESTION_FIELD_TYPES, QUESTION_WIDGET_TYPES, \
    OTHER_BALE_CATEGORY_NAME
from fir_userinteraction.helpers import build_userinteraction_path
from incidents.models import Incident, IncidentCategory, Label, SEVERITY_CHOICES, BusinessLine, BaleCategory, Comments


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
    title = models.CharField(max_length=500, null=True, blank=True)
    label = models.CharField(max_length=500, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        label_str = self.label if self.label else 'NO LABEL, PLEASE CHANGE'
        return '{} | required: {}'.format(label_str, self.required)


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
    answer_value = models.TextField(blank=True)

    def __str__(self):
        return '{} - Question: "{}"'.format(self.question.label, self.quiz.id)


# Watchlist for any action performed
class QuizWatchListItem(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, blank=True, null=True)
    business_line = models.ForeignKey(BusinessLine, on_delete=models.CASCADE, blank=True, null=True,
                                      help_text='Business Line for the watchlist')

    def __str__(self):
        return '{} - Quiz: "{}", incident: {}'.format(self.business_line.name, self.quiz.id, self.quiz.incident.id)


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


class AutoNotifyDuration(models.Model):
    duration = models.DurationField()
    severity = models.IntegerField(choices=SEVERITY_CHOICES)
    category = models.ForeignKey(IncidentCategory)

    def __str__(self):
        return 'category: {}| severity: {}'.format(self.category, self.severity)


# Helper methods
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


def create_artifact_for_incident(incident, artifact_type, artifact_value):
    """
    Create an artifact for an incident with the specified type and value
    :param incident:
    :param artifact_type:
    :param artifact_value:
    :return:
    """
    return incident.artifacts.create(type=artifact_type, value=artifact_value)


def get_artifacts_for_incident(incident):
    """
    Return a dictionary mapping artifact types to values for this specific incident
    :param incident: incident model
    :return: dict of artifacts
    """
    return {artifact.type: artifact.value for artifact in incident.artifacts.all()}


def get_or_create_global_category():
    """
    This is the global category of incidents, used to store some of the common notifications
    :return: global incident category DB entity
    """

    try:
        bale_category = BaleCategory.objects.get(name=OTHER_BALE_CATEGORY_NAME)
    except BaleCategory.DoesNotExist:
        bale_category = BaleCategory.objects.create(name=OTHER_BALE_CATEGORY_NAME, category_number=0)
    try:
        return IncidentCategory.objects.get(name=GLOBAL_CATEGORY_NAME, bale_subcategory=bale_category)
    except IncidentCategory.DoesNotExist:
        return IncidentCategory.objects.create(name=GLOBAL_CATEGORY_NAME, bale_subcategory=bale_category)


def create_comment_for_answered_quiz(quiz, request):
    """
    Take the quiz and the request and build the 'user answered comment'
    :param quiz: The quiz db entity
    :param request: The current django request
    """
    user = request.user if request.user is not None else 'AnonymousUser'
    ip = get_ip(request)

    quiz_url = build_userinteraction_path(request, quiz.incident_id)
    full_user = '{}@{}'.format(str(user), str(ip))

    incident = quiz.incident
    incident.status = 'O'
    incident.save()
    Comments.objects.create(incident=quiz.incident,
                            comment='An incident form has been filled in: <{}>.\n The user that commented is: {}'.format(
                                quiz_url,
                                full_user),
                            action=get_or_create_label('User Answered'),
                            opened_by=user)

