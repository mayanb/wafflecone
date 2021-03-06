# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-22 23:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0107_team_timezone'),
    ]

    operations = [
        migrations.CreateModel(
            name='Pin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_trashed', models.BooleanField(db_index=True, default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('all_product_types', models.BooleanField(default=False)),
                ('process_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pins', to='ics.ProcessType')),
                ('product_types', models.ManyToManyField(to='ics.ProductType')),
                ('userprofile', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='pins', to='ics.UserProfile')),
            ],
        ),
    ]
