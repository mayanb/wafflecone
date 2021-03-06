# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-07 23:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0115_merge_20180711_2257'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskfile',
            name='extension',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='taskfile',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='ics.Task'),
        ),
    ]
