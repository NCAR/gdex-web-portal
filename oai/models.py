from django.db import models

from wagtail.admin.panels import FieldPanel
from wagtail import blocks
from wagtail.fields import StreamField
from wagtail.models import Page


class MetadataFormat(blocks.StructBlock):
    prefix = blocks.CharBlock(
            required=True, max_length=30, default="",
            help_text="Prefix for this metadata format")
    schema = blocks.CharBlock(
            required=True, max_length=255, default="",
            help_text="XML schema for this metadata format")
    namespace = blocks.CharBlock(
            required=True, max_length=255, default="",
            help_text="XML namespace of schema for this metadata format")


class MetadataFormatsPage(Page):
    metadata_formats = StreamField(
            [('metadata_format', MetadataFormat())],
            block_counts={'metadata_format': {'min_num': 0}},
            use_json_field=True,
            default="List of exportable metadata formats")
    content_panels = Page.content_panels + [
        FieldPanel('metadata_formats', classname="collapsible collapsed")
    ]
    is_creatable = False
