# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-06-30 00:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0112_merge_20180625_2059'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskattribute',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]