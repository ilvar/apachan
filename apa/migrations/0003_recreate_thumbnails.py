# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import easy_thumbnails.files

from django.conf import settings
from django.db import migrations

from apa.utils import get_datetime


def save_thumb(image_path, thumb_path):
    root_image_path = os.path.join(settings.MEDIA_ROOT, image_path)
    root_thumb_path = os.path.join(settings.MEDIA_ROOT, thumb_path)

    thumber = easy_thumbnails.files.get_thumbnailer(open(root_image_path), relative_name=image_path)

    thumb = thumber.generate_thumbnail({'size': (200, 0), 'crop': 'smart', 'sharpen': True})
    thumb.image.save(root_thumb_path)


def recrate_thumbnails(apps, schema_editor):
    Image = apps.get_model('apa', 'Image')

    for image in Image.objects.all():
        str_dt = get_datetime(image.datetime).strftime("%Y%m/%d")
        image_path = "%s/%s.%s" % (str_dt, image.text_id, image.extension or "jpg")
        image_full_path = os.path.join("images", image_path)
        thumb_path = os.path.join("thumbs", image_path)

        try:
            save_thumb(image_full_path, thumb_path)
        except IOError:
            print('Missed file: %s' % image_path)


class Migration(migrations.Migration):
    dependencies = [
        ('apa', '0002_auto_20170616_0016'),
    ]

    operations = [
        migrations.RunPython(recrate_thumbnails),
    ]
