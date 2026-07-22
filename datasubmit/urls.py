from django.urls import path
from . import views

urlpatterns = [
    # Entry point: explains the two-stage process, links into the Advisor below.
    path('datasubmit/', views.data_submission_welcome, name='data-submission-welcome'),

    # Stage 1: the Submission Advisor -- five quick questions that route the
    # user to either GDEX's own form (below) or an external repository like Zenodo.
    path('datasubmit/advisor/', views.submission_advisor, name='data-submission-advisor'),
    path(
        'datasubmit/advisor/zenodo-recommendation/',
        views.data_submission_zenodo_recommendation,
        name='data-submission-zenodo-recommendation',
    ),
    path(
        'datasubmit/advisor/zenodo-next-steps/',
        views.data_submission_zenodo_next_steps,
        name='data-submission-zenodo-next-steps',
    ),
    path(
        'datasubmit/advisor/gdex-next-steps/',
        views.data_submission_gdex_next_steps,
        name='data-submission-gdex-next-steps',
    ),

    # Stage 2: the actual GDEX submission form -- basic info, contributors,
    # access info, and terms, reached only after the Advisor routes here.
    path('datasubmit/gdex-submission-form/confirmation/', views.submission_confirmation, name='data-submission-confirmation'),
    path(
        'datasubmit/gdex-submission-form/contributors/',
        views.data_submission_contributors,
        name='data-submission-contributors',
    ),
    path('datasubmit/gdex-submission-form/<slug:step_slug>/', views.gdex_submission_form_step, name='data-submission-step'),
]
