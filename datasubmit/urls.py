from django.urls import path
from . import views

urlpatterns = [
    path('submitportal/', views.data_submission_portal, name='data-submission-portal'),
    path('submitportal/view-mode/', views.data_submission_portal_set_view_mode, name='data-submission-portal-view-mode'),
    path('submitportal/dataset/<int:pk>/', views.data_submission_portal_view, name='data-submission-portal-view'),
    path('submitportal/dataset/<int:pk>/files/', views.data_submission_portal_files, name='data-submission-portal-files'),
    path('submitportal/dataset/<int:pk>/metadata/', views.data_submission_portal_metadata, name='data-submission-portal-metadata'),
    path('submitportal/messages/', views.data_submission_portal_messages, name='data-submission-portal-messages'),
    path('submitportal/budget/', views.data_submission_portal_budget, name='data-submission-portal-budget'),
    path('submitportal/proposal-templates/', views.data_submission_portal_proposal_templates, name='data-submission-portal-proposal-templates'),

    # Entry point: explains the two-stage process, links into the Advisor below.
    # Lives at submitportal/submit/ so the whole flow renders inside the portal
    # sidebar (portal_base.html) rather than as a standalone public page.
    path('submitportal/submit/', views.data_submission_welcome, name='data-submission-welcome'),
    # Stage 1: the Submission Advisor -- five quick questions that route the
    # user to either GDEX's own form (below) or an external repository like Zenodo.
    path('submitportal/submit/advisor/', views.submission_advisor, name='data-submission-advisor'),
    path(
        'submitportal/submit/advisor/zenodo-recommendation/',
        views.data_submission_zenodo_recommendation,
        name='data-submission-zenodo-recommendation',
    ),
    path(
        'submitportal/submit/advisor/zenodo-next-steps/',
        views.data_submission_zenodo_next_steps,
        name='data-submission-zenodo-next-steps',
    ),
    path(
        'submitportal/submit/advisor/gdex-next-steps/',
        views.data_submission_gdex_next_steps,
        name='data-submission-gdex-next-steps',
    ),

    # Stage 2: the actual GDEX submission form -- basic info, contributors,
    # access info, and terms, reached only after the Advisor routes here.
    path('submitportal/submit/gdex-submission-form/confirmation/', views.submission_confirmation, name='data-submission-confirmation'),
    path(
        'submitportal/submit/gdex-submission-form/contributors/',
        views.data_submission_contributors,
        name='data-submission-contributors',
    ),
    path('submitportal/submit/gdex-submission-form/<slug:step_slug>/', views.gdex_submission_form_step, name='data-submission-step'),
]
