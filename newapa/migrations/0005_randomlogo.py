# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-19 21:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newapa', '0004_auto_20170118_1856'),
    ]

    operations = [
        migrations.CreateModel(
            name='RandomLogo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='random/logos/')),
            ],
        ),
    ]
