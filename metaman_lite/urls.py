from django.urls import path
from . import views


urlpatterns = [
    path("", views.start, {'token': None}),
    path("token/<token>/", views.start),
]
