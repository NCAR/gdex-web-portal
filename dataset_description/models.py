from django.db import models

from wagtail.core.models import Page
from wagtail.core.fields import RichTextField


class DatasetDescriptionPage(Page):
    dsid = models.CharField(max_length=5, blank=False, default="", unique=True)
    dsdoi = models.CharField(max_length=50, blank=True, default="")
    dstype = models.CharField(max_length=1, blank=False, default="")
    dslogo = models.CharField(max_length=255, blank=True, default="")
    dstitle = models.CharField(max_length=255, blank=False, default="")
    update_freq = models.CharField(max_length=50, blank=True, default="")
    abstract = RichTextField(blank=False, default="")
    temporal = models.JSONField(blank=False, default=dict)
    temporal_freq = models.CharField(max_length=255, blank=True, default="")
    variables = models.JSONField(blank=False, default=dict)
    levels = models.JSONField(blank=True, default=dict)
    data_types = models.JSONField(blank=True, default=list)
    spatial_coverage = models.JSONField(blank=True, default=dict)
    contributors = models.JSONField(blank=False, default=list)
    volume = models.JSONField(blank=False, default=dict)
    data_formats = models.JSONField(blank=False, default=list)
    related_rsrc_list = models.JSONField(blank=True, default=list)
    related_dslist = models.JSONField(blank=True, default=list)
    publications = models.JSONField(blank=True, default=list)
    access_restrict = RichTextField(blank=True, default="")
    usage_restrict = RichTextField(blank=True, default="")
    acknowledgement = RichTextField(blank=True, default="")
    data_license = models.JSONField(blank=False, default=dict)

    is_creatable = False
