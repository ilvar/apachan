# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-06-16 00:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apa', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='captcha',
            name='num_used',
            field=models.IntegerField(default=0, editable=False),
        ),
    ]
