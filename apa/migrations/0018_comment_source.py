# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-11 19:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apa', '0017_auto_20170302_2029'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='source',
            field=models.TextField(blank=True, null=True),
        ),
    ]
