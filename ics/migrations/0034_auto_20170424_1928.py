# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-24 19:28
from __future__ import unicode_literals

import django.contrib.postgres.search
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0033_auto_20170420_1702'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='search',
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
    ]