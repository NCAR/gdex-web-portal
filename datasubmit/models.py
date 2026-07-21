from django.db import models

SUBMISSION_TYPE_CHOICES = [
    ('own', 'I am submitting my own dataset'),
    ('recommend', 'I am recommending a dataset for the GDEX repository'),
]


class Submission(models.Model):
    submission_type = models.CharField(max_length=20, choices=SUBMISSION_TYPE_CHOICES, default='own')
    # Placeholder for the GDEX dataset ID (e.g. 'd123456') assigned once a
    # submission is accepted and archived. Not yet set anywhere in the
    # wizard -- staff will need to populate it out-of-band until that part
    # of the workflow exists.
    dsid = models.CharField(max_length=10, default='', blank=True)
    dataset_title = models.CharField(max_length=500, default='')
    dataset_abstract = models.CharField(max_length=5000, default='')
    dataset_details = models.CharField(max_length=5000, default='')
    dataset_size_mb = models.FloatField(default=0)
    hpc_access = models.BooleanField(default=False)
    cif_fare_contributors = models.BooleanField(default=False)
    is_ncar_employee = models.BooleanField(default=False)

    data_policy_agreement = models.BooleanField(default=False)
    data_deposit_agreement = models.BooleanField(default=False)

    def __str__(self):
        return self.dataset_title


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
    access_verification = models.CharField(
        max_length=20,
        choices=[
            ('', 'Not verified'),
            ('readable', 'Verified readable (/glade)'),
            ('reachable', 'Verified reachable (https)'),
        ],
        default='',
        blank=True,
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.location
