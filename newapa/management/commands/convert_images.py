# coding=utf-8
import os

from django.core.management.base import BaseCommand

from apa.models import Image


class Command(BaseCommand):
    help = 'Creates Django images from existing ones'

    def handle(self, *args, **options):
        img_qs = Image.objects.filter(img_hash__isnull=True)
        cnt = img_qs.count()
        for i, img in enumerate(img_qs):
            if os.path.exists(img.get_absolute_path()):
                img.save()

            if i % 10000 == 0:
                print "Done %s of %s" % (i, cnt)
