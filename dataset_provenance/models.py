from django.db import models
from wagtail.core import blocks
from wagtail.core.fields import StreamField
from wagtail.core.models import Page
from wagtail.admin.edit_handlers import StreamFieldPanel

# Create your models here.

class EventSection(blocks.StructBlock):
    start_date = blocks.DateBlock(
        required=True,
        help_text="Start date for the event"
    )
    end_date = blocks.DateBlock(
        required=False,
        help_text="End date for the event, or blank for single date, or same as start date to indicate only a year/month"
    )
    source_institution = blocks.CharBlock(
        required=False,
        max_length=255,
        help_text="Name of institution that provided/processed the data"
    )
    description = blocks.RichTextBlock(
        required=True,
        features = [
            'h2', 'h3', 'bold', 'italic', 'ol', 'ul', 'hr', 'link', 'image', 'superscript', 'subscript'
        ],
        help_text="A description of the event"
    )

class DatasetProvenancePage(Page):
    dsid = models.CharField(max_length=5, blank=False, default="", unique=True)
    events = StreamField(
        [
            ('event_section', EventSection()),
        ],
        block_counts = {
            'event_section': {'min_num': 1},
        },
        default="",
        verbose_name = "List of Event Sections"
    )

    content_panels = Page.content_panels + [
        StreamFieldPanel('events', classname="collapsible collapsed"),
    ]

    is_creatable = False
