# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-01-31 22:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0017_auto_20170126_2141'),
    ]

    operations = [
        migrations.AddField(
            model_name='processtype',
            name='x',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='processtype',
            name='y',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
