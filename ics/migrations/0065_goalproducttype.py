# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-07 01:49
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0064_merge_20171204_2120'),
    ]

    operations = [
        migrations.CreateModel(
            name='GoalProductType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('goal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='goal_product_types', to='ics.Goal')),
                ('product_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ics.ProductType')),
            ],
        ),
    ]
