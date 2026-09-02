from django.conf import settings
from django.db import models
from django.utils import timezone


class Submission(models.Model):
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)
    # Submissio type is now is_wishlist with False being their "own" dataset
    is_wishlist = models.BooleanField(default=False)
    dsid = models.CharField(max_length=7, default='', blank=True)
    dataset_size_mb = models.FloatField(default=-9999)

    def __str__(self):
        pre_submission = self.pre_submissions.first()
        return pre_submission.dataset_title if pre_submission else f'Submission #{self.pk}'

class PreSubmission(models.Model):
    """The descriptive/decision fields a submitter fills out about their
    dataset -- split out from Submission so Submission itself can stay a
    lean record of status/ownership. FK'd as to-many for schema
    flexibility, but the wizard (views/submit.py) only ever creates one
    per Submission."""
    submission = models.ForeignKey(Submission, related_name='pre_submissions', on_delete=models.CASCADE)
    dataset_title = models.CharField(max_length=500, default='')
    dataset_abstract = models.CharField(max_length=5000, default='')
    dataset_details = models.CharField(max_length=5000, default='')
    hpc_access = models.BooleanField(default=False)
    cif_fare_contributors = models.BooleanField(default=False)
    is_ncar_employee = models.BooleanField(default=False)
    data_policy_agreement = models.BooleanField(default=False)
    data_deposit_agreement = models.BooleanField(default=False)

    def __str__(self):
        return self.dataset_title
class SubmissionStatus(models.Model):
    class Status(models.TextChoices):
        PENDING_DECISION = 'pending_decision', 'Pending Decision'
        IN_PROGRESS = 'in_progress', 'In Progress'
        IN_REVIEW = 'in_review', 'In Review'
        PUBLISHED = 'published', 'Published'
        CANCELED = 'canceled', 'Canceled'
        DELETED = 'deleted', 'Deleted'
    submission = models.ForeignKey(Submission, related_name='status_history', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_DECISION)
    order = models.PositiveIntegerField(default=9999)
    timestamp = models.DateTimeField(default=timezone.now)
    
class DatasetLocation(models.Model):
    """One place GDEX can find the dataset -- most submissions have exactly
    one, but the wizard allows a second for data split across locations
    (see AccessInfoForm's dataset_location/dataset_location_2). A separate
    row per location, rather than flat columns on Submission, so the schema
    doesn't hardcode a max of two even though the current UI does."""
    submission = models.ForeignKey(Submission, related_name='locations', on_delete=models.CASCADE)
    location = models.CharField(max_length=500, default='')
    access_method = models.CharField(max_length=20, default='')
    # What kind of check GDEX's check-access service passed at submission
    # time -- these mean genuinely different things, so it's not a plain
    # True/False: 'readable' means a /glade path was recursively scanned and
    # every file under it was confirmed readable; 'reachable' means an https
    # URL responded to a request (no scan, no file count). Blank for access
    # methods that aren't checked at all (ftp/sftp, s3, doi, other). The
    # wizard hard-gates submission on this check, so a saved row can never
    # hold a failed/unreadable/unreachable state -- only these three.
    
    #Split old access verification field into 2 different fields
    readable =  models.BooleanField(default=False)
    reachable = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_checking = models.BooleanField(default=False)
    data_size = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=9999)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.location
