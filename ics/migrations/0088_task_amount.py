# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-20 18:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0087_auto_20180320_1828'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='amount',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=10),
        ),
    ]
