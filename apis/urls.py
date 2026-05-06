from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from api.urls import urlpatterns as _api_urlpatterns

_EXCLUDED = {'clear_cache/', 'jira-event/'}
_public = [
    p for p in _api_urlpatterns
    if not any(str(p.pattern).startswith(prefix) for prefix in _EXCLUDED)
]

urlpatterns = [
    re_path(r'^citations(\..*?){0,1}/', include('apis.citations.urls')),
    path('schema/', SpectacularAPIView.as_view(patterns=_public), name='subdomain-schema'),
    path('schema/documentation/', SpectacularSwaggerView.as_view(url_name='subdomain-schema'), name='subdomain-swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='subdomain-schema'), name='subdomain-redoc'),
] + _public
