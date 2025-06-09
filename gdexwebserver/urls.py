from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

from . import views
from search import views as search_views
from home import views as home_views

urlpatterns = [
#    path('django-admin/', admin.site.urls),
    path('admin/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    re_path(r'^citations(\..*?){0,1}/', include("apis.citations.urls"), name='output_format'),
    path('contact-us/', views.contact_us),
    path('dssearch/', search_views.dssearch),
    path('search/', search_views.search, name='search'),
    path('resources/', include('daas.urls')),
    path('api/', include('api.urls')),
    path('metrics/', include('home.urls')),
    path('datasets/', include('datasets.urls')),
    #path('login/', include('login.urls')),
    path('globus/', include('globus.urls')),
    path('gsearch/', include('gsearch.urls')),
    path('oai/', include("oai.urls")),
    path('lookfordata/', include('lookfordata.urls')),
    path('metaman/', include('metaman.urls')),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    re_path(r'^accounts/profile/$', login_required(TemplateView.as_view(template_name='account/profile.html')), name='user_profile'),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns = urlpatterns + [
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path("", include(wagtail_urls)),

    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
]
