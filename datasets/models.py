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
