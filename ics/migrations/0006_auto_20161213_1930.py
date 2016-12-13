# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-12-13 19:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0005_auto_20161208_2025'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='notes',
        ),
        migrations.AddField(
            model_name='task',
            name='labelIndex',
            field=models.PositiveSmallIntegerField(default=0, editable=False),
        ),
        migrations.AlterField(
            model_name='task',
            name='is_open',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='label',
            field=models.CharField(editable=False, max_length=20),
        ),
    ]
