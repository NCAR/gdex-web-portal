from django.urls import path
from . import views
from django.views.generic import RedirectView

urlpatterns = [
    path('mylogout', views.logout),
    path('', RedirectView.as_view(url='/ajax/#!cgi-bin/dashboard')),
    path('newtoken', views.newtoken),
]
