# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-01 18:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0034_auto_20170424_1928'),
    ]

    operations = [
        migrations.AddField(
            model_name='attribute',
            name='is_trashed',
            field=models.BooleanField(default=False),
        ),
    ]