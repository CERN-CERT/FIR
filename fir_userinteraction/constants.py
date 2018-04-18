"""
Constants defined for various usages, to avoid hard-coding of strings in the app
"""

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
