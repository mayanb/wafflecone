# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-03 20:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0106_merge_20180428_0016'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='timezone',
            field=models.CharField(default=b'US/Pacific', max_length=50),
        ),
    ]
