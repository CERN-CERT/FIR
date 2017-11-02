from django import forms


class TestForm(forms.Form):
    your_name = forms.CharField(max_length=100, label='Your name')
    incident_type = forms.CharField(max_length=100, label='Incident type', disabled=True)
