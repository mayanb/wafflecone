# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-12-13 19:31
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0007_delete_labelindex'),
    ]

    operations = [
        migrations.RenameField(
            model_name='task',
            old_name='labelIndex',
            new_name='label_index',
        ),
    ]
