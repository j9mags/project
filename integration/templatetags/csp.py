from django import template


register = template.Library()


@register.filter(name='get')
def get(od, key):
    return od.get(key)
