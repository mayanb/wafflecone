# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-06-18 23:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0109_team_task_label_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='time_format',
            field=models.CharField(choices=[('m', 'military'), ('n', 'normal')], default='n', max_length=1),
        ),
    ]
