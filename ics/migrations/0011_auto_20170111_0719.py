# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-01-11 07:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0010_auto_20170110_2322'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='display',
            field=models.CharField(blank=True, max_length=25),
        ),
        migrations.AlterField(
            model_name='taskattribute',
            name='value',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
