# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-30 19:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0088_input_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='is_generic',
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
