# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-23 21:28
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('newapa', '0006_favorite'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModerationLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=64)),
                ('comment_id', models.CharField(max_length=64)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('moderator', models.CharField(max_length=64)),
            ],
        ),
    ]
