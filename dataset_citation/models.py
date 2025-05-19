from django.db import models
from wagtail.models import Page

# Create your models here.



class DatasetCitationPage(Page):
    dsid = models.CharField(max_length=9, blank=False, default="", unique=True)
    num_citations = models.IntegerField(blank=False, default=0)
    citations = models.JSONField(blank=True, default=list)

    is_creatable = False
