from django.db import models

from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail import blocks
from wagtail.admin.panels import FieldPanel

# Create your models here.


class MetamanPage(Page):
    is_creatable = False


class MenuItem(blocks.StructBlock):
    title = blocks.CharBlock(
            required=True, max_length=30, default="",
            help_text="Title of this menu action")
    description = blocks.CharBlock(
            required=True, max_length=255, default="",
            help_text="Brief description (255 chars max) of this menu action")
    requires_existing_dsid = blocks.BooleanBlock(
            required=False, default=False,
            help_text=("Check this box if an existing dataset ID is required "
                       "for this action"))


class MetamanCategoryPage(Page):
    tab_title = models.CharField(
            blank=False, max_length=100, default="",
            verbose_name="Title of the tab for this category")
    menu = StreamField(
            [('menu_item', MenuItem()),],
            block_counts={'menu_item': {'min_num': 0},},
            default="", use_json_field=True,
            verbose_name="Menu of actions for this category")
    content_panels = Page.content_panels + [
        FieldPanel('tab_title', classname="collapsible collapsed"),
        FieldPanel('menu', classname="collapsible collapsed"),
    ]
    is_creatable = True
