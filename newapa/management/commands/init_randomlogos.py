# coding=utf-8
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from newapa.models import RandomLogo


class Command(BaseCommand):
    help = 'Recreates randompacks existing in 1.0'

    def handle(self, *args, **options):
        old_path = os.path.join(settings.MEDIA_ROOT, 'random', 'sitelogo')

        RandomLogo.objects.all().delete()

        for fname in os.listdir(old_path):
            if fname in ['.', '..']:
                continue

            fname_clean = fname.decode('ascii', errors='ignore').encode('ascii', errors='ignore')
            RandomLogo.objects.create(image='/' + os.path.join('random', 'sitelogo', fname_clean))
