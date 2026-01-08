#import logging
from django.db import models
from wagtail.search import index
from wagtail.models import Page
from wagtail.fields import RichTextField
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    InlinePanel
)
from wagtail.contrib.forms.models import (
    AbstractFormField,
    AbstractForm,
)

#logger = logging.getLogger(__name__)
# Create your models here.

class FormField(AbstractFormField):
    page = ParentalKey(
        'DaasForm',
        on_delete=models.CASCADE,
        related_name='form_fields'
    )

class DaasForm(AbstractForm):
    short_description = models.CharField(max_length=250)
    body = RichTextField(blank=True)

    search_fields = AbstractForm.search_fields + [
        index.SearchField('short_description'), 
        index.SearchField('body')
    ]

    content_panels = AbstractForm.content_panels + [
        FieldPanel('short_description'), 
        InlinePanel('form_fields', label='Form Fields', classname='form-control'),
        FieldPanel('body', classname='full')
    ]
    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        # iterate through the fields in the generated form
        for name, field in form.fields.items():
            # for all fields, get any existing CSS classes and add 'form-control'
            # ensure the 'class' attribute is a string of classes with spaces
            css_classes = field.widget.attrs.get('class', '').split()
            css_classes.append('form-control')
            field.widget.attrs.update({'class': ' '.join(css_classes)})
        return form


class DaasHome(Page):
    # Database fields
    body = RichTextField(blank=True)
    additional_information = RichTextField(blank=True)
 
    # Editor panels configuration
    content_panels = Page.content_panels + [
        FieldPanel('body', classname='full'),
        FieldPanel('additional_information', classname='full')
    ]


class DaasBasicPage(Page):
    # Database fields
    body = RichTextField(blank=True)
    additional_information = RichTextField(blank=True)
 
    # Editor panels configuration
    content_panels = Page.content_panels + [
        FieldPanel('body', classname='full'),
        FieldPanel('additional_information', classname='full')
    ]

