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


FIELD_MAPPINGS = {
    'django.forms.BooleanField': {
        'on': True,
        'off': False
    }
}

ALERT_CLASSES = {
    'labels': {
        'Opened': 'alert alert-info',
        'Closed': 'alert alert-success',
        'Info': 'alert alert-info',
        'Monitor': 'alert alert-warning',
        'Alerting': 'alert alert-success',
        'Takedown': 'alert alert-warning',
        'User Answered': 'alert alert-default',
        'Investigation': 'alert alert-info',
        'Abuse': 'alert alert-danger',
        'Blocked': 'alert alert-danger',
        'Initial': 'alert alert-success',
    },
    'glyphs': {
        'Opened': 'glyphicon glyphicon-plus',
        'Closed': 'glyphicon glyphicon-remove',
        'Info': 'glyphicon glyphicon-info-sign',
        'Monitor': 'glyphicon glyphicon-eye-open',
        'Alerting': 'glyphicon glyphicon-exclamation-sign',
        'Takedown': 'glyphicon glyphicon-envelope',
        'User Answered': 'glyphicon glyphicon-envelope',
        'Investigation': 'glyphicon glyphicon-zoom-in',
        'Abuse': 'glyphicon glyphicon-flag',
        'Blocked': 'glyphicon glyphicon-ban-circle',
        'Initial': 'glyphicon glyphicon-envelope',
    }
}


QUIZ_ANSWER_CATEGORY_TEMPLATE = 'quiz_answer'