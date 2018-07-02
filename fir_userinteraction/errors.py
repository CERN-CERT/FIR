import sys

from django import http
from django.template.exceptions import TemplateDoesNotExist
from django.template import loader
from django.utils.encoding import force_text
from django.views.decorators.csrf import requires_csrf_token


@requires_csrf_token
def permission_denied(request, template_name='userinteraction/403.html'):
    """
    403 error handler

    @param request: The django request
    @param template_name: The name of the 403 template, defaults to this app's 403.html
    """
    _, value, _ = sys.exc_info()
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return http.HttpResponseForbidden('<h1>Forbidden (403)</h1>', content_type='text/html')
    return http.HttpResponseForbidden(
        template.render(request=request, context={'exception': force_text(value)})
    )


@requires_csrf_token
def internal_server_error(request, template_name="userinteraction/500.html"):
    """
    500 error handler.

    @param request: The django request
    @param template_name: The name of the tempate to use, defaults to this app's 500.html
    """
    _, value, _ = sys.exc_info()
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return http.HttpResponseServerError('<h1>Server Error (500)</h1>', content_type='text/html')
    return http.HttpResponseServerError(template.render(request=request, context={'exception': force_text(value)}))


@requires_csrf_token
def not_found(request, template_name="userinteraction/404.html"):
    """
    404 error handler

    @param request: The django request
    @param template_name: The name of the 404 message template, defaults to this app's 404.html
    """
    _, value, _ = sys.exc_info()
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return http.HttpResponseNotFound('<h1>Not found (404)</h1>', content_type='text/html')
    return http.HttpResponseNotFound(template.render(request=request, context={'exception': force_text(value)}))
