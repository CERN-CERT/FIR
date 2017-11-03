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
from .models import Quiz

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


def build_dynamic_form(field_dict, data=None):
    dyn_form = type('DynForm',  # form name is irrelevant
                    (forms.BaseForm,),
                    {'base_fields': field_dict})

    return dyn_form(data=data)


def build_form_field(question):
    field_dict = {}
    field_type = import_from_module(question.field_type)
    widget_type = None
    if question.widget_type:
        widget_type = import_from_module(question.widget_type)
    field_dict['id'] = str(question.id)
    field_dict['field'] = field_type(widget=widget_type, label=question.label, required=question.required)
    return field_dict


def build_form_from_questions(questions, quiz_type):
    fields = map(build_form_field, questions)
    form_fields = {}
    for field in fields:
        form_fields[field['id']] = field['field']
    form_fields['quiz_type'] = forms.CharField(widget=forms.HiddenInput(), required=False, initial=str(quiz_type))
    return build_dynamic_form(form_fields)


@require_http_methods(['GET', 'POST'])
def get_quiz_by_id(request, id):
    user_quiz = get_object_or_404(Quiz, id=id)
    form_questions = user_quiz.template.questions.all()
    form = build_form_from_questions(form_questions, user_quiz.template.category.id)

    return render(request, 'userinteraction/name.html', {'form': form, 'quiz': user_quiz})


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
    form_questions = user_quiz.template.questions.all()
    form = build_form_from_questions(form_questions, user_quiz.template.category.id)

    return render(request, 'userinteraction/name.html', {'form': form, 'quiz': user_quiz})


# API related stuff
class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)

    class Meta:
        fields = '__all__'
