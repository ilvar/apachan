# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-11 19:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cookie_id', models.CharField(editable=False, max_length=255)),
                ('ip', models.CharField(editable=False, max_length=255)),
                ('type', models.CharField(choices=[('post', 'post'), ('validation', 'validation')], editable=False, max_length=255)),
                ('dt', models.DateTimeField(auto_now_add=True)),
                ('message', models.CharField(editable=False, max_length=255)),
                ('data', models.TextField(blank=True, editable=False)),
            ],
        ),
    ]
