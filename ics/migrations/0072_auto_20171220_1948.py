# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-20 19:48
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0071_alert_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='last_seen',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='send_emails',
            field=models.BooleanField(default=True),
        ),
    ]
