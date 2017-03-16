# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-03-16 21:56
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0026_auto_20170315_2201'),
    ]

    operations = [
        migrations.AlterField(
            model_name='processtype',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name='User',
        ),
    ]
