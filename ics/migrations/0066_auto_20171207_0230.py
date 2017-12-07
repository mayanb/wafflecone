# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-07 02:30
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0065_goalproducttype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='goal',
            name='product_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='goals', to='ics.ProductType'),
        ),
        migrations.AlterField(
            model_name='goalproducttype',
            name='product_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='goal_product_types', to='ics.ProductType'),
        ),
    ]
