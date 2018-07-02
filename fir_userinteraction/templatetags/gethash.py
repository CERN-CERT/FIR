from django import template

register = template.Library()

@register.filter
def gethash(h, key):
    if key in h:
        return h[key]
    return None