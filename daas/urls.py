from django.urls import path
from . import views

urlpatterns = [
    path('daas/my_submissions/', views.my_submissions),
    path('daas/user_submissions/', views.user_submissions),
    path(r'daas/get_full_submission/', views.full_submission),
    path(r'daas/accept/', views.accept),
    path(r'daas/reject/', views.reject)
]
