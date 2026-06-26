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


@register.filter
def location_tree(buckets):
    """Group flat location buckets into a continent > region > country tree.

    Each bucket value is a GCMD-style string like:
      "CONTINENT > NORTH AMERICA > UNITED STATES OF AMERICA"
      "OCEAN > ATLANTIC OCEAN"
      "GEOGRAPHIC REGION > ARCTIC"

    Returns a list of top-level groups, each containing mid-level child groups:
      [
        { 'label': 'CONTINENT', 'direct': [...], 'children': [
            { 'label': 'NORTH AMERICA', 'buckets': [<bucket>, ...] },
            ...
        ]},
        ...
      ]
    Direct buckets are those with only one level (top-level match with no sub-region).
    """
    tree = {}
    order = []
    for bucket in (buckets or []):
        value = bucket.get('value') if isinstance(bucket, dict) else getattr(bucket, 'value', '')
        parts = [p.strip() for p in str(value).split('>')]

        top = parts[0] if parts else 'Other'
        mid = parts[1] if len(parts) > 1 else None

        if top not in tree:
            tree[top] = {'direct': [], 'children': {}, 'child_order': []}
            order.append(top)

        if mid:
            if mid not in tree[top]['children']:
                tree[top]['children'][mid] = []
                tree[top]['child_order'].append(mid)
            tree[top]['children'][mid].append(bucket)
        else:
            tree[top]['direct'].append(bucket)

    result = []
    for top_label in order:
        top_data = tree[top_label]
        children = [
            {'label': mid_label, 'buckets': top_data['children'][mid_label]}
            for mid_label in top_data['child_order']
        ]
        result.append({
            'label': top_label,
            'direct': top_data['direct'],
            'children': children,
        })
    return result


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
