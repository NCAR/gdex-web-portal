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
def get_facet(facets, field_name):
    """Return the facet dict/object with the given field_name from a facets list, or None."""
    for f in (facets or []):
        name = f.get('field_name') if isinstance(f, dict) else getattr(f, 'field_name', None)
        if name == field_name:
            return f
    return None

@register.filter
def checked_value(facet):
    """Return the value of the first checked bucket in a facet, or ''."""
    try:
        buckets = facet.get('buckets') if isinstance(facet, dict) else getattr(facet, 'buckets', [])
    except Exception:
        return ''
    for b in (buckets or []):
        checked = b.get('checked') if isinstance(b, dict) else getattr(b, 'checked', False)
        if checked:
            return b.get('value') if isinstance(b, dict) else getattr(b, 'value', '')
    return ''

# Help text for the info-icon tooltip shown next to a facet's header.
# Keyed by field_name; a facet with no entry here gets no tooltip icon.
FACET_TOOLTIPS = {
    'gcmd_topics_and_terms': (
        "Keywords are high level concepts describing a topic or subject "
        "area following the NASA GCMD Earth Science Keyword vocabulary - "
        "e.g. Atmosphere (topic), Clouds (subtopic of Atmosphere)."
    ),
    'gcmd_variables': (
        "Variables are more specifically defined subcategories of "
        "keywords following the NASA GCMD Earth Science Keyword "
        "vocabulary. These are measured variables and parameters that "
        "specifically describe data."
    ),
}

@register.simple_tag
def facet_tooltip(field_name):
    """Return the info-tooltip help text for a facet field_name, or '' if none is defined."""
    return FACET_TOOLTIPS.get(field_name, '')

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
