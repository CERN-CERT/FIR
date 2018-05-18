import logging

from django import template

register = template.Library()


@register.filter
def index(l, i):
    try:
        return l[int(i) - 1]
    except IndexError:
        logging.error('Invalid index {} for array of length {}'.format(int(i) - 1, len(l)))
    return ''


@register.filter
def index_empty_str_for_none(list, idx):
    try:
        item = list[int(idx) - 1]
        if item:
            return item
    except IndexError:
        logging.error('Invalid index {} for array of length {}'.format(int(idx) - 1, len(list)))
    return ''
