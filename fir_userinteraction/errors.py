import sys

from django import http
from django.template.exceptions import TemplateDoesNotExist
from django.template import loader
from django.utils.encoding import force_text
from django.views.decorators.csrf import requires_csrf_token


@requires_csrf_token
def permission_denied(request, template_name='userinteraction/403.html'):
    _, value, _ = sys.exc_info()
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return http.HttpResponseForbidden('<h1>403 Forbidden</h1>', content_type='text/html')
    return http.HttpResponseForbidden(
        template.render(request=request, context={'exception': force_text(value)})
    )

