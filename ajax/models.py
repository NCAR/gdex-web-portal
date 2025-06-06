from django.db import models

from wagtail.models import Page

# Create your models here.

class AjaxPage(Page):
    is_creatable = False
