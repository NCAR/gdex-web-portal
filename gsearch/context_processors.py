from django.conf import settings

def settings_variables(request):
    return {
        'SEARCH_TEMPLATE_DIR': settings.BASE_TEMPLATES,
        # Add more settings variables as needed
    }
