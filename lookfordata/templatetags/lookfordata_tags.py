from django import template


register = template.Library()

@register.filter
def new_browse_value(get_request):
#    if 'b' in get_request or not 'nb' in get_request:
#        return ""
#    return get_request['nb'];
     if 'b' in get_request:
         return ''
     return 'y'
