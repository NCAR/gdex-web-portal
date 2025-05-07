import os
import sys

from datetime import date

from django import template
from home.models import DecsStaff, AlertMessage, SocialMedia

register = template.Library()

# DecsStaff snippets
@register.inclusion_tag('unity/decs_staff.html', takes_context=True)
def decs_staff(context):
    return {
        'decs_staff': DecsStaff.objects.all(),
        'request': context['request'],
    }

# AlertMessage snippets
@register.inclusion_tag('unity/alerts.html', takes_context=True)
def alerts(context):
    return {
        'alerts': AlertMessage.objects.all(),
        'request': context['request'],
    }

# SocialMedia snippets
@register.inclusion_tag('unity/social_footer.html', takes_context=True)
def social(context):
    return {
        'social': SocialMedia.objects.all(),
        'request': context['request'],
    }

@register.simple_tag
def check_date(start, end):
    """ This tag takes a start and end date as input 
        and evaluates whether the current date is within
        the two dates.  Input dates are datetime.date
        instances.  """

    now = date.today()
    if (start <= now) and (end >= now):
        return True
    else:
        return False

@register.filter
def check_dir(path):
    """ Checks whether a directory path exists """
    return os.path.isdir(path)

@register.filter
def check_file(path):
    """ Checks whether a directory path exists """
    return os.path.isfile(path) or os.path.islink(path)
