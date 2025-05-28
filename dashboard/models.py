from django.db import models

from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
import sys

# Create your models here.

class DashboardButtonPosition(blocks.ChoiceBlock):
    choices = [
        ("TR", "Top/Right"),
        ("BR", "Bottom/Right"),
    ]

def validate_button_position(value):
    sys.stderr.write("value is " + str(value) + "\n")
    if value is None:
        raise ValidationError("You must make a choice from the menu.")

class DashboardSection(blocks.StructBlock):
    section_label = blocks.CharBlock(required=True, max_length=30, default="", help_text="Title for the section in the dashboard")
    button_label = blocks.CharBlock(required=False, max_length=20, default="", help_text="Text of an optional button for the section")
    button_position = blocks.ChoiceBlock(required=True, choices=DashboardButtonPosition.choices, default=DashboardButtonPosition.choices[0], blank=False, validators=[validate_button_position], help_text="Position of the optional button for the section (Top/Right is the default)")

class DashboardPage(Page):
    dashboard_sections = StreamField(
            [('dashboard_section', DashboardSection()),],
            block_counts={'dashboard_section': {'min_num': 1},},
            default="", use_json_field=True,
            verbose_name="List of Dashboard Sections")
    content_panels = Page.content_panels + [
        FieldPanel('dashboard_sections', classname="collapsible collapsed"),
    ]
    is_creatable = False
