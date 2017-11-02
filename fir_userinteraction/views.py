from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django import forms
from .forms import TestForm

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
        'txt1message': forms.CharField(widget=forms.Textarea, label='Tell us about your browsing activity in the last day'),
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
def build_dynamic_form(field_dict, data=None):
    dyn_form = type('DynForm',  # form name is irrelevant
                    (forms.BaseForm,),
                    {'base_fields': field_dict})

    return dyn_form(data=data)
