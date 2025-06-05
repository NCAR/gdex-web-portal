from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    def handle(self, *args, **options):
        user = get_user_model()
        su = user.objects.filter(is_superuser=True)
        if len(su) == 0:
            user.objects.create_superuser(
                    username=settings.DJANGO_SUPERUSER['username'],
                    email=settings.DJANGO_SUPERUSER['email'],
                    password=settings.DJANGO_SUPERUSER['password'])
