# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-28 22:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0048_attribute_datatype'),
    ]

    operations = [
        migrations.AddField(
            model_name='processtype',
            name='description',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='producttype',
            name='description',
            field=models.CharField(default='', max_length=100),
        ),
    ]