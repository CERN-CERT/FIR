import six
from django import forms
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms.utils import ErrorDict
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_http_methods

from fir_userinteraction.constants import ALERT_CLASSES
from fir_userinteraction.helpers import import_from_module
from incidents.authorization.decorator import authorization_required
from incidents.models import Incident, Comments, Label
from .models import Quiz, QuizAnswer, get_incident_for_user, get_or_create_quiz, \
    create_comment_for_answered_quiz


# Form building functions
def build_dynamic_form(field_dict, form_id=None, get_class=None, data=None):
    class_name = 'DynForm'
    if form_id:
        class_name = 'DynForm{}'.format(form_id)
    dyn_form = type(class_name,  # form name is irrelevant
                    (forms.BaseForm,),
                    {'base_fields': field_dict})

    if get_class:
        return dyn_form
    else:
        return dyn_form(data=data)


def build_form_field(question, readonly):
    field_dict = {}
    field_type = import_from_module(question.field_type)
    widget_type = None
    if question.widget_type:
        widget_type = import_from_module(question.widget_type)
    field_dict['id'] = str(question.id)
    field_dict['field'] = field_type(widget=widget_type, label=mark_safe(question.label), required=False,
                                     disabled=readonly)
    return field_dict


def build_form_from_questions(questions, form_id, readonly):
    fields = map(lambda q: build_form_field(q, readonly), questions)
    form_fields = {}
    for field in fields:
        form_fields[field['id']] = field['field']
    return build_dynamic_form(form_fields, form_id=form_id, get_class=True)


def get_ordering_fields(question_group):
    """
    Get the fields on which to order the formsets

    :param question_group: The question group from the database, containing all the orderings
    :return: a list of the order of the fields in the form
    """
    orderings = list(question_group.quizgroupquestionorder_set.all().order_by('order_index'))
    ordering_fields = []
    for ordering in orderings:
        ordering_fields.append(str(ordering.question.id))
    return ordering_fields


def build_form_from_template(question_group, request=None, readonly=False, initial=None):
    questions = question_group.questions.all()
    form_class = build_form_from_questions(questions, question_group.id, readonly)

    if not request:
        built = form_class(prefix='{}'.format(str(question_group.id)), initial=initial)
    else:
        built = form_class(request.POST, prefix='{}'.format(str(question_group.id)), initial=initial)

    built.order_fields(get_ordering_fields(question_group))
    setattr(built, 'description', question_group.description)
    return built


def extract_form_answers(question_group, formset):
    answers = {}
    for question in question_group.questions.all():
        # Get the question with this id from the current question group
        form_question_keys = filter(
            lambda x: x.startswith(str(question_group.id)) and x.endswith('-{}'.format(question.id)), formset.data)
        answer = formset.data[form_question_keys[0]] if len(form_question_keys) > 0 else None
        if answer:
            answers[question.id] = unicode(answer)
    return answers


def validate_formset(question_group, formset):
    if question_group.required:
        answers = extract_form_answers(question_group, formset)
        # Needed to unset all of the errors
        formset._errors = ErrorDict()
        formset.cleaned_data = formset.data

        if not (any(answers)) or not ('on' in six.itervalues(answers)):
            return False
    return True


def save_answers(request, quiz, question_groups, formsets):
    for i in range(len(question_groups)):
        group = question_groups[i]
        answers = extract_form_answers(group, formsets[i])
        for k, v in answers.iteritems():
            question = group.questions.get(id=k)
            answer = QuizAnswer.objects.create(question=question, question_group=group, quiz=quiz, answer_value=v)
            print('Created answer: {}'.format(str(answer)))

    quiz.is_answered = True
    quiz.save()
    create_comment_for_answered_quiz(quiz, request)


def get_ordered_question_groups(quiz):
    return map(lambda x: x.question_group,
               quiz.template.quiztemplatequestiongrouporder_set.all().order_by('order_index'))


def get_device_artifact_from_quiz(quiz):
    """
    Get a quiz's incident and get the device if it exists in the artifacts
    :param quiz: Quiz object from the database
    :return: a string containing the name (if defined), or None in case it does not exist
    """
    device_artifacts = quiz.incident.artifacts.filter(type='device')
    if device_artifacts:
        return device_artifacts[0].value.upper()
    else:
        return None


def render_quiz(request, quiz):
    question_groups = get_ordered_question_groups(quiz)
    device_artifact = get_device_artifact_from_quiz(quiz)
    formsets = []
    if request.method == 'GET':
        for group in question_groups:
            formsets.append(build_form_from_template(group))
        return render(request, 'userinteraction/quiz-sets.html', {
            'formsets': formsets,
            'names': map(lambda x: x.title, question_groups),
            'quiz': quiz,
            'alert_classes': ALERT_CLASSES,
            'device_artifact': device_artifact,
            'comments': quiz.incident.comments_set.order_by('-date')
        })
    else:
        # POST case
        validations = []
        for group in question_groups:
            formsets.append(build_form_from_template(group, request=request))
            is_valid = validate_formset(group, formsets[-1])
            validations.append(is_valid)
            if not is_valid:
                formsets[-1].add_error(None, 'At least one checkbox needs to be ticked!')
        if len(filter(lambda x: x is False, validations)) > 0:
            return render(request, 'userinteraction/quiz-sets.html', {
                'formsets': formsets,
                'names': map(lambda x: x.title, question_groups),
                'quiz': quiz,
                'device_artifact': device_artifact,
                'comments': quiz.incident.comments_set.order_by('-date')
            })
        else:
            # All forms are valid, save the answer and return readonly quiz
            save_answers(request, quiz, question_groups, formsets)
            return redirect('userinteraction:quiz', id=quiz.id)


def render_answered_quiz(request, quiz):
    question_groups = get_ordered_question_groups(quiz)
    is_incident_handler = (request.user.is_superuser or
                           request.user.groups.filter(name='Incident handlers').count() > 0)

    device_artifact = get_device_artifact_from_quiz(quiz)
    answers = QuizAnswer.objects.filter(quiz=quiz)
    formsets = []
    for group in question_groups:
        group_answers = answers.filter(question_group=group)
        answer_dict = {str(answer.question.id): answer.answer_value for answer in group_answers}
        formsets.append(build_form_from_template(group, readonly=True, initial=answer_dict))

    return render(request, 'userinteraction/quiz-sets.html',
                  {'formsets': formsets,
                   'names': map(lambda x: x.title, question_groups),
                   'quiz': quiz,
                   'device_artifact': device_artifact,
                   'comments': quiz.incident.comments_set.order_by('-date'),
                   'alert_classes': ALERT_CLASSES,
                   'is_incident_handler': is_incident_handler})


# ================================================================================ HTTP VIEWS FROM HERE ON

@require_http_methods(['GET', 'POST'])
def get_quiz_by_id(request, id):
    user_quiz = get_object_or_404(Quiz, id=id)
    answered = user_quiz.is_answered
    if answered and request.method == 'POST':
        return HttpResponse(status=400, content='This form has already been filled in!!')
    if answered is False:
        return render_quiz(request, user_quiz)
    else:
        return render_answered_quiz(request, user_quiz)


@require_http_methods(['GET', 'POST'])
@login_required
@authorization_required('incidents.view_incidents', Incident, view_arg='incident_id')
def get_quiz_by_incident(request, incident_id, authorization_target=None):
    incident = get_incident_for_user(authorization_target, incident_id, request)

    quiz = get_or_create_quiz(request, incident)
    answered = quiz.is_answered
    if answered is True:
        return render_answered_quiz(request, quiz)
    return render_quiz(request, quiz)


def get_quizzes_from_incidents(incidents):
    return map(lambda x: x.quiz, incidents)


@require_http_methods(['GET'])
@login_required
def show_all_quizzes(request):
    permissions = 'incidents.view_incidents'
    incident_list = Incident.authorization.for_user(request.user, permissions).filter(~Q(quiz=None))

    opened = incident_list.filter(status='O').order_by('-severity', '-date')
    blocked = incident_list.filter(status='B').order_by('-severity', '-date')
    closed = incident_list.filter(status='C').order_by('-date', '-severity')

    return render(request, 'userinteraction/quiz-list.html', {
        'opened': get_quizzes_from_incidents(opened),
        'blocked': get_quizzes_from_incidents(blocked),
        'closed': get_quizzes_from_incidents(closed)
    })


@require_http_methods(['POST'])
@login_required
@authorization_required('incidents.view_incidents', Incident, view_arg='incident_id')
def comment_on_quiz(request, incident_id, authorization_target=None):
    quiz = get_object_or_404(Quiz, incident_id=incident_id)
    comment = request.POST['comment']
    if comment:
        Comments.objects.create(incident=quiz.incident,
                                comment=comment,
                                action=Label.objects.get(name='Alerting', group__name='action'),
                                opened_by=request.user)

    return redirect('userinteraction:quiz-by-incident', incident_id=incident_id)
