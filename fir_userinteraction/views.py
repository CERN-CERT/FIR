from importlib import import_module

from django import forms
from django.contrib.auth.decorators import login_required
from django.forms.utils import ErrorDict
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from fir_api.permissions import IsIncidentHandler
from fir_userinteraction.serializers import QuizSerializer
from incidents.authorization.decorator import authorization_required
from incidents.models import Incident
from .models import Quiz, QuizAnswer, QuizTemplate, model_updated

FIELD_MAPPINGS = {
    'django.forms.BooleanField': {
        'on': True,
        'off': False
    }
}


# Utility function
def import_from_module(full_name):
    class_name = full_name.split('.')[-1]
    module_name = '.'.join(full_name.split('.')[:-1])
    return getattr(import_module(module_name), class_name)


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
    field_dict['field'] = field_type(widget=widget_type, label=question.label, required=False, disabled=readonly)
    return field_dict


def build_form_from_questions(questions, form_id, readonly):
    fields = map(lambda q: build_form_field(q, readonly), questions)
    form_fields = {}
    for field in fields:
        form_fields[field['id']] = field['field']
    # form_fields['quiz_type'] = forms.CharField(widget=forms.HiddenInput(), required=False, initial=str(quiz_type))
    return build_dynamic_form(form_fields, form_id=form_id, get_class=True)


def build_form_from_template(question_group, request=None, readonly=False, initial=None):
    questions = question_group.questions.all()
    form_class = build_form_from_questions(questions, question_group.id, readonly)
    if not request:
        return form_class(prefix='{}'.format(str(question_group.id)), initial=initial)
    else:
        return form_class(request.POST, prefix='{}'.format(str(question_group.id)), initial=initial)


def extract_form_answers(question_group, formset):
    answers = {}
    for question in question_group.questions.all():
        # Get the question with this id from the current question group
        form_question_keys = filter(
            lambda x: x.startswith(str(question_group.id)) and x.endswith('-{}'.format(question.id)), formset.data)
        answer = formset.data[form_question_keys[0]] if len(form_question_keys) > 0 else None
        if answer:
            answers[question.id] = str(answer)
    return answers


def validate_formset(question_group, formset):
    if question_group.required:
        answers = extract_form_answers(question_group, formset)
        # Needed to unset all of the errors
        formset._errors = ErrorDict()
        formset.cleaned_data = formset.data
        if not (any(answers)) or not ('on' in answers.itervalues()):
            return False
    return True


def save_answers(request, quiz, question_groups, formsets):
    for i in xrange(len(question_groups)):
        group = question_groups[i]
        answers = extract_form_answers(group, formsets[i])
        for k, v in answers.iteritems():
            question = group.questions.get(id=k)
            answer = QuizAnswer.objects.create(question=question, question_group=group, quiz=quiz, answer_value=v)
            print('Created answer: {}'.format(str(answer)))

    quiz.is_answered = True
    quiz.user = request.user
    quiz.save()
    model_updated.send(sender=quiz.__class__, instance=quiz, request=request)


def render_quiz(request, quiz):
    question_groups = quiz.template.question_groups.all()
    formsets = []
    if request.method == 'GET':
        for group in question_groups:
            formsets.append(build_form_from_template(group))
        return render(request, 'userinteraction/quiz-sets.html',
                      {'formsets': formsets, 'names': map(lambda x: x.title, question_groups), 'quiz': quiz})
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
            return render(request, 'userinteraction/quiz-sets.html',
                          {'formsets': formsets, 'names': map(lambda x: x.title, question_groups), 'quiz': quiz})
        else:
            # All forms are valid, save the answer and return readonly quiz
            save_answers(request, quiz, question_groups, formsets)
            return redirect('userinteraction:quiz', id=quiz.id)


def render_answered_quiz(request, quiz):
    print('Rendering answered quiz')
    question_groups = quiz.template.question_groups.all()
    answers = QuizAnswer.objects.filter(quiz=quiz)
    formsets = []
    for group in question_groups:
        group_answers = answers.filter(question_group=group)
        answer_dict = {str(answer.question.id): answer.answer_value for answer in group_answers}
        print(answer_dict)
        formsets.append(build_form_from_template(group, readonly=True, initial=answer_dict))

    return render(request, 'userinteraction/quiz-sets.html',
                  {'formsets': formsets, 'names': map(lambda x: x.title, question_groups), 'quiz': quiz,
                   'thanks': 'This form is already answered, you are seeing a read-only view of the completed form.'})


def get_or_create_quiz(incident):
    try:
        user_quiz = Quiz.objects.get(incident_id=incident.id)
    except Quiz.DoesNotExist:
        template = get_object_or_404(QuizTemplate, category=incident.category)
        user_quiz = Quiz.objects.create(template=template, incident=incident)
    return user_quiz


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
    if authorization_target is None:
        incident = get_object_or_404(
            Incident.authorization.for_user(request.user, 'incidents.view_incidents'),
            pk=incident_id)
    else:
        incident = authorization_target

    quiz = get_or_create_quiz(incident)
    answered = quiz.is_answered
    if answered and request.method == 'POST':
        return HttpResponse(status=400, content='This form has already been filled in!!')
    if answered is False:
        return render_quiz(request, quiz)
    else:
        return render_answered_quiz(request, quiz)


@require_http_methods(['GET'])
@login_required
def show_all_quizzes(request):
    user_quizzes = Quiz.objects.filter(user=request.user)
    return render(request, 'userinteraction/quiz-list.html', {'quizzes': user_quizzes})


# API related stuff
class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)

    class Meta:
        fields = '__all__'
