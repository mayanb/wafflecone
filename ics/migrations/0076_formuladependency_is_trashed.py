# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-09 20:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0075_formulaattribute_formuladependency_taskformulaattribute'),
    ]

    operations = [
        migrations.AddField(
            model_name='formuladependency',
            name='is_trashed',
            field=models.BooleanField(default=False),
        ),
    ]
