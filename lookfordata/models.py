from django.db import models
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail import blocks
from wagtail.admin.panels import FieldPanel


class FilterData(blocks.StructBlock):
    id = blocks.CharBlock(required=True, max_length=10, default="")
    title = blocks.CharBlock(required=True, max_length=30, default="")
    description = blocks.CharBlock(required=True, default="")
    query_table = blocks.CharBlock(required=False, max_length=50,
        default="",
        help_text="Absolute name of database table for dataset queries")


class LookForDataPage(Page):
    refine_filters = StreamField(
            [('filter_data', FilterData()),],
            block_counts={'filter_data': {'min_num': 1},},
            default="", use_json_field=True,
            verbose_name="List of Refine Filters")
    results_title = models.CharField(blank=False, max_length=100, default="",
        verbose_name="Title for Results Pane")
    content_panels = Page.content_panels + [
        FieldPanel('refine_filters', classname="collapsible collapsed"),
        FieldPanel('results_title', classname="collapsible collapsed"),
    ]
    is_creatable = False
