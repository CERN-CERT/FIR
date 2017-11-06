from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponse, get_object_or_404
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from fir_api.permissions import IsIncidentHandler
from fir_userinteraction.serializers import QuizSerializer
from incidents.authorization.decorator import authorization_required
from incidents.models import Incident
from .models import Quiz, QuestionGroup
from django.forms import formset_factory
from django.forms.utils import ErrorDict

from importlib import import_module

FIELDS_DICT = {
    'spam': {
        '1question1': forms.BooleanField(widget=forms.CheckboxInput, label='Did you give your password to anyone?'),
        '2message': forms.CharField(widget=forms.Textarea,
                                    label='Tell us about websites that you registered for recently'),
        '3extra_comments': forms.CharField(widget=forms.Textarea, label='Anything extra to add?'),
        'quiz_type': forms.CharField(widget=forms.HiddenInput(), required=False, initial='spam')
    },
    'malware': {
        'question1': forms.BooleanField(widget=forms.CheckboxInput, label='Did you try installing an antivirus?'),
        'question2': forms.BooleanField(widget=forms.CheckboxInput,
                                        label='Did you try turning your computer on and off again?'),
        'question3': forms.BooleanField(widget=forms.CheckboxInput,
                                        label='Did you click any suspicious links?'),
        'txt1message': forms.CharField(widget=forms.Textarea,
                                       label='Tell us about your browsing activity in the last day'),
        'extra_comments': forms.CharField(widget=forms.Textarea, label='Anything extra to add?'),
        'quiz_type': forms.CharField(widget=forms.HiddenInput(), required=False, initial='malware')

    }
}

ALLOWED_FIELDS = ['spam', 'malware']


# Create your views here.
def get_name(request):
    if request.method == 'POST' and 'quiz_type' in request.POST:
        form = build_dynamic_form(FIELDS_DICT[request.POST['quiz_type']], request.POST)
        print('Valid: {}'.format(form.is_valid()))
        print('Bound: {}'.format(form.is_bound))
        print('Data: {}'.format(form.data))
        return render(request, 'userinteraction/name.html',
                      {'form': form, 'thanks': 'Thank you for filling in the form!'})

    else:
        fields_dict = {}
        if 'type' in request.GET and request.GET['type'] in ALLOWED_FIELDS:
            fields_dict = FIELDS_DICT[request.GET['type']]
        form = build_dynamic_form(fields_dict)
        return render(request, 'userinteraction/name.html', {'form': form})


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


def build_form_field(question):
    field_dict = {}
    field_type = import_from_module(question.field_type)
    widget_type = None
    if question.widget_type:
        widget_type = import_from_module(question.widget_type)
    field_dict['id'] = str(question.id)
    field_dict['field'] = field_type(widget=widget_type, label=question.label, required=False)
    return field_dict


def build_form_from_questions(questions, form_id):
    fields = map(build_form_field, questions)
    form_fields = {}
    for field in fields:
        form_fields[field['id']] = field['field']
    # form_fields['quiz_type'] = forms.CharField(widget=forms.HiddenInput(), required=False, initial=str(quiz_type))
    return build_dynamic_form(form_fields, form_id=form_id, get_class=True)


def build_form_from_template(question_group, form_id, request=None):
    questions = question_group.questions.all()
    form_class = build_form_from_questions(questions, form_id)
    if not request:
        return form_class(prefix='{}'.format(str(question_group.id)))
    else:
        return form_class(request.POST, prefix='{}'.format(str(question_group.id)))


def validate_formset(db_form, formset):
    if db_form.required:
        answers = {}
        for question in db_form.questions.all():
            # Get the question with this id from the current question group
            form_question_keys = filter(
                lambda x: x.startswith(str(db_form.id)) and x.endswith('-{}'.format(question.id)), formset.data)
            answer = formset.data[form_question_keys[0]] if len(form_question_keys) > 0 else None
            if answer:
                answers[question.id] = str(answer)

        # Needed to unset all of the errors
        formset._errors = ErrorDict()
        formset.cleaned_data = formset.data
        if not (any(answers)) or not ('on' in answers.itervalues()):
            return False
    return True


@require_http_methods(['GET', 'POST'])
def get_quiz_by_id(request, id):
    user_quiz = get_object_or_404(Quiz, id=id)
    return render_quiz(request, user_quiz)


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

    print(incident)
    user_quiz = get_object_or_404(Quiz, incident_id=incident.id)
    return render_quiz(request, user_quiz)


def render_quiz(request, user_quiz):
    question_groups = user_quiz.template.question_groups.all()
    formsets = []
    if request.method == 'GET':
        for group in question_groups:
            formsets.append(build_form_from_template(group, group.id))
        return render(request, 'userinteraction/quiz-sets.html',
                      {'formsets': formsets, 'names': map(lambda x: x.title, question_groups), 'quiz': user_quiz})
    else:
        # POST case
        validations = []
        for group in question_groups:
            formsets.append(build_form_from_template(group, group.id, request=request))
            is_valid = validate_formset(group, formsets[-1])
            validations.append(is_valid)
            if not is_valid:
                formsets[-1].add_error(None, 'At least one checkbox needs to be ticked!')

        print(validations)
        if len(filter(lambda x: x is False, validations)) > 0:
            return render(request, 'userinteraction/quiz-sets.html',
                          {'formsets': formsets, 'names': map(lambda x: x.title, question_groups), 'quiz': user_quiz})
        else:
            return render(request, 'userinteraction/quiz-sets.html',
                          {'formsets': formsets, 'names': map(lambda x: x.title, question_groups), 'quiz': user_quiz,
                           'thanks': 'Thanks for filling in the form! Your answer has been recorded'})


# API related stuff
class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)

    class Meta:
        fields = '__all__'
