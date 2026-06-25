from django import template
from django.conf import settings

register = template.Library()


@register.filter
def has_active_bucket(facet):
    """Return True if any bucket in the facet is currently checked/selected."""
    try:
        buckets = facet.get('buckets') if isinstance(facet, dict) else getattr(facet, 'buckets', [])
    except Exception:
        return False
    for b in (buckets or []):
        checked = b.get('checked') if isinstance(b, dict) else getattr(b, 'checked', False)
        if checked:
            return True
    return False


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
