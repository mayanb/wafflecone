# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-11 17:19
from __future__ import unicode_literals

import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0093_processtype_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='processtype',
            name='keywords',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='processtype',
            name='search',
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
        migrations.AddField(
            model_name='producttype',
            name='keywords',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='producttype',
            name='search',
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
        migrations.AddIndex(
            model_name='processtype',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search'], name='ics_process_search_3b6a57_gin'),
        ),
        migrations.AddIndex(
            model_name='producttype',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search'], name='ics_product_search_35552a_gin'),
        ),
    ]
