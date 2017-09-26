# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-27 16:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0040_auto_20170619_2152'),
    ]

    operations = [
        migrations.AddField(
            model_name='processtype',
            name='default_amount',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='item',
            name='amount',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=10),
        ),
    ]