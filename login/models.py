import binascii
import os

from datetime import datetime
from datetime import timedelta

from django.db import models
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User

from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel

# Create your models here.

class LoginPage(Page):
    reg_intro = RichTextField(blank=False, default="",
        verbose_name='Registration Introduction')
    tou_url = models.URLField(blank=False, default="",
        verbose_name="URL for UCAR's Terms of Service")
    pass_msg = RichTextField(blank=False, default="",
        verbose_name='Message for Password Reset')

    content_panels = Page.content_panels + [
        FieldPanel('reg_intro', classname="collapsible collapsed"),
        FieldPanel('tou_url', classname="collapsible collapsed"),
        FieldPanel('pass_msg', classname="collapsible collapsed"),
    ]
    is_creatable = False




  
def generate_token():
    """Generates a random token"""
    return binascii.hexlify(os.urandom(14)).decode()
    

def generate_valid_date():
    """Generates a date a fixed number of days after today."""
    valid_duration = timedelta(days=360)
    return datetime.today() + valid_duration

class UserToken(models.Model):
    value = models.CharField(max_length=32, default=generate_token)
    valid_until = models.DateTimeField(default=generate_valid_date)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    def token_expired(self):
        """Returns True if today's date is greater than valid_to."""
        return self.valid_to < datetime.today()

    def generate_new_token(self):
        self.value = generate_token()
        self.valid_until = generate_valid_date()
        self.save()
        return (self.value, self.valid_until)
   
