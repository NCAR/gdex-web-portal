class APISubdomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.META.get('HTTP_HOST', '').split(':')[0]
        if host.startswith('api.'):
            request.urlconf = 'apis.urls'
        return self.get_response(request)
