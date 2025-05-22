from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def truncate_facet(value, separator='>', num=1):
    """ Split a facet string value by the given separator,
        and return the last num element(s) joined by the separator.

        Example usage in template:
        {% truncate_facet 'a > b > c > d' %}                       # returns 'd'
        {% truncate_facet 'a > b > c > d' separator='>', num=2 %}  # returns 'c > d'
        {% truncate_facet 'a > b > c > d' separator='>', num=1 %}  # returns 'd'
        {% truncate_facet 'a > b > c > d' separator='>', num=0 %}  # returns 'a > b > c > d'
    """
    if not value:
        return ''
    if isinstance(value, list):
        return value[-num:]
    if isinstance(value, str):
        value_list = value.split(separator)
        if len(value_list) > num:
            return separator.join(value_list[-num:]).strip()
        else:
            return value
    return value
