"""
Constants defined for various usages, to avoid hard-coding of strings in the app
"""

OTHER_BALE_CATEGORY_NAME = 'Other'
GLOBAL_CATEGORY_NAME = 'Global'

QUESTION_FIELD_TYPES = (
    ('django.forms.CharField', 'Char'),
    ('django.forms.BooleanField', 'Bool')
)

QUESTION_WIDGET_TYPES = (
    ('django.forms.Textarea', 'Text Area'),
    ('django.forms.CheckboxInput', 'Check Box')
)

USERS_BL = 'Users'
GROUPS_BL = 'Groups'

INCIDENT_VIEWERS_ROLE = 'Incident viewers'
