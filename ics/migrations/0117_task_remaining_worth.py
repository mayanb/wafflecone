# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-07-24 21:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0116_merge_20180711_2338'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='remaining_worth',
            field=models.DecimalField(decimal_places=3, max_digits=10, null=True),
        ),
    ]
