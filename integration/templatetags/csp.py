from django import template

import locale
locale.setlocale(locale.LC_ALL, 'de_DE.utf8')

register = template.Library()


@register.filter(name='get')
def get(od, key):
    return od.get(key)


@register.filter()
def currency(value):
    value = value or 0
    return locale.currency(value, grouping=True)
