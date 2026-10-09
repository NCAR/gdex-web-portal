from django.urls import path
from . import views
from django.views.generic import RedirectView

urlpatterns = [
    path('mylogout', views.logout),
    path('', RedirectView.as_view(url='/dashboard/')),
    path('signup/', views.signup, name='account_signup'),
    path('newtoken', views.newtoken),
]
