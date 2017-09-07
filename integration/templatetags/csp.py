from django import template

import locale
locale.setlocale(locale.LC_ALL, 'de')

register = template.Library()


@register.filter(name='get')
def get(od, key):
    return od.get(key)


@register.filter()
def currency(value):
    return locale.currency(value, grouping=True)
