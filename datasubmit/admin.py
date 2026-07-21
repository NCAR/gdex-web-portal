from django.contrib import admin

from .models import DatasetLocation, Submission


class DatasetLocationInline(admin.TabularInline):
    model = DatasetLocation
    extra = 0


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'dsid',
        'dataset_title',
        'submission_type',
        'data_policy_agreement',
    )
    list_filter = ('submission_type',)
    search_fields = ('dataset_title', 'locations__location')
    inlines = [DatasetLocationInline]


@admin.register(DatasetLocation)
class DatasetLocationAdmin(admin.ModelAdmin):
    # submission_id alongside submission itself -- multiple test submissions
    # share the same dataset_title, so the title alone doesn't disambiguate
    # which Submission row a location belongs to.
    list_display = ('id', 'submission_id', 'submission', 'location', 'access_method', 'access_verification', 'order')
    list_filter = ('access_method', 'access_verification', 'submission')
