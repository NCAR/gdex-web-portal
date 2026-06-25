from django.db import models

from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel


class DatasetsPage(Page):
    header = models.CharField(
        max_length=100,
        blank=False,
        default="",
        help_text="The label for the list of datasets",
    )
    description = RichTextField(
        blank=True,
        default="",
        help_text="An optional description to appear above the list of datasets",
    )

    content_panels = Page.content_panels + [
        FieldPanel('header', classname="collapsible collapsed"),
        FieldPanel('description', classname="collapsible collapsed"),
    ]

    def get_children(self):
        return Page.objects.child_of(self).live().order_by('slug')

class CustomSubsetPage(Page):
    dsid = models.CharField(
        max_length=7,
        blank=False,
        default="",
        help_text="The dataset ID for which this custom subset page is associated",
    )
    gindex = models.IntegerField(
        blank=True,
        null=True,
        help_text="The group index for which this custom subset page is associated (optional)",
    )
    header = models.CharField(
        max_length=100,
        blank=False,
        default="",
        help_text="The header label or title for the custom subset page",
    )
    description = RichTextField(
        blank=True,
        default="",
        help_text="An optional description to appear above the custom subset form",
    )

    content_panels = Page.content_panels + [
        FieldPanel('dsid', classname="collapsible collapsed"),
        FieldPanel('gindex', classname="collapsible collapsed"),
        FieldPanel('header', classname="collapsible collapsed"),
        FieldPanel('description', classname="collapsible collapsed"),
    ]