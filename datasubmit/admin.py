from django.contrib import admin

from .models import DatasetLocation, PreSubmission, Submission, SubmissionStatus


class DatasetLocationInline(admin.TabularInline):
    model = DatasetLocation
    extra = 0


class PreSubmissionInline(admin.TabularInline):
    model = PreSubmission
    fk_name = 'submission'
    extra = 0


class SubmissionStatusInline(admin.TabularInline):
    model = SubmissionStatus
    fk_name = 'submission'
    extra = 0


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'dsid',
        'dataset_title',
        'is_wishlist',
    )
    list_filter = ('is_wishlist',)
    search_fields = ('pre_submissions__dataset_title', 'locations__location')
    inlines = [PreSubmissionInline, DatasetLocationInline, SubmissionStatusInline]

    @admin.display(description='Dataset Title')
    def dataset_title(self, obj):
        pre_submission = obj.pre_submissions.first()
        return pre_submission.dataset_title if pre_submission else ''


@admin.register(PreSubmission)
class PreSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'submission_id', 'dataset_title', 'is_ncar_employee', 'data_policy_agreement')
    list_filter = ('is_ncar_employee', 'cif_fare_contributors', 'hpc_access')


@admin.register(DatasetLocation)
class DatasetLocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'submission_id', 'location', 'access_method', 'readable', 'reachable', 'order')
    list_filter = ('access_method', 'readable', 'reachable', 'submission_id')


@admin.register(SubmissionStatus)
class SubmissionStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'submission_id', 'status', 'order', 'timestamp')
    list_filter = ('status',)
