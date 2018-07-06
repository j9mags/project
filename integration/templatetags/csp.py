from django import template
from django.conf import settings

import locale
locale.setlocale(locale.LC_ALL, settings.LOCALE)

register = template.Library()


@register.filter(name='get')
def get(od, key):
    return od.get(key)


@register.filter()
def currency(value):
    value = value or 0
    return locale.currency(value, grouping=True)


@register.filter()
def classname(obj):
    return obj.__class__.__name__
