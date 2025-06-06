from datetime import timedelta
from datetime import datetime
import http
import urllib

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.http.cookie import SimpleCookie
from login.models import UserToken
from api import common



class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Temp fix to address not having token on signup
        #try:
        #    print(str(dir(sociallogin.user.usertoken)))
        #except:
        #    ut = UserToken(user=sociallogin.user)
        #    ut.save()
        return super(MySocialAccountAdapter, self).pre_social_login(
            request, sociallogin
        )

    #def save_user(self, request, user, form):
    #    print('Creating new user')
    #    print(dir(user.user))
    #    token = UserToken(user=user.user)
    # 
    #    return super(MySocialAccountAdapter, self).save_user(
    #        request, user, form
    #    )
        
    
class MyAccountAdapter(DefaultAccountAdapter):
    def post_login(self, request, user, *, email_verification,
                   signal_kwargs, email, signup, redirect_url):
        """Adds cookies after login.
        """
        response = super(MyAccountAdapter, self).post_login( 
                request, user, email_verification=email_verification, 
                signal_kwargs=signal_kwargs, email=email, signup=signup, redirect_url=redirect_url
        )
        http.cookies._quote = lambda x: x # Hack: remove when unquote cookie logic is changed in dashboard.
        self.generate_cookies(user.email, response)
        return response

    def logout(self, request):
        super(MyAccountAdapter, self).logout(request)

    def remove_cookies(self, reponse):
         response.delete_cookie('duser')
         response.delete_cookie('ruser')
         response.delete_cookie('dpass')
    
    def generate_cookies(self, email, response):
        #email = urllib.parse.quote(email)
        
        # Using set_cookie is not compatible with legacy login due to adding quotes around the cookie value.
        age = timedelta(days=100) ## This will be required for set_cookie in django 4.2
        age=60*60*24*100
        response.set_cookie('duser',value=email,max_age=age, domain=None)
        response.set_cookie('ruser',value=email,max_age=age, domain=None)
        response.set_cookie('dpass',value=email,max_age=age, domain=None)
        
        # Set special cookie for superusers
        superusers = [a['email'] for a in common.get_staff()]
        if email in superusers:
            cookie_value = email+settings.ICOOKIE['content']
            response.set_cookie(settings.ICOOKIE['id'],value=cookie_value,max_age=age, domain=None)
     
