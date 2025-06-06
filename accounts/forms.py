from allauth.socialaccount.forms import SignupForm
from django import forms
from django.utils.crypto import get_random_string
from django.shortcuts import redirect
from django.urls import reverse
import login.models as lm
import api.common as common
 
 
class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, label='First Name')
    last_name = forms.CharField(max_length=30, label='Last Name')
    email = forms.EmailField(label='Email Address')

    first_name.widget.attrs.update({"class": "form-control"})
    last_name.widget.attrs.update({"class": "form-control"})
    email.widget.attrs.update({"class": "form-control"})
    
    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)
        first_name = forms.CharField(max_length=30, label='First Name')
        last_name = forms.CharField(max_length=30, label='Last Name')
        email = forms.EmailField(label='Email Address')
        self.fields['email2'] = forms.EmailField(label='Confirm Email')
        self.fields['email2'].widget.attrs.update({"class": "form-control"})
        
    def save(self, request):
        try:
            user = super(CustomSignupForm, self).save(request)
        except ValueError:
            return redirect(reverse("/account/profile"), permanent=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        token = lm.UserToken(user=user)
        token.save()
        common.add_new_user(user.email, user.first_name, user.last_name)
        return user

#class UserAccountAdapter(DefaultAccountAdapter):
#
#    def save_user(self, request, user, form, commit=True):
#        """
#        This is called when saving user via allauth registration.
#        We override this to set additional data on user object.
#        """
#        # Do not persist the user yet so we pass commit=False
#        # (last argument)
#        user = super(UserAccountAdapter, self).save_user(request, user, form, commit=False)
#        #user.age = form.cleaned_data.get('age')
#        user.save()
