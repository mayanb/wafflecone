# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-06 01:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0089_auto_20180405_2227'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=3, default=1, max_digits=10)),
                ('process_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ics.ProcessType')),
                ('product_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ics.ProductType')),
            ],
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instructions', models.TextField()),
                ('process_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipes', to='ics.ProcessType')),
                ('product_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipes', to='ics.ProductType')),
            ],
        ),
        migrations.CreateModel(
            name='TaskIngredient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=3, default=1, max_digits=10)),
                ('ingredient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ics.ProductType')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ics.Task')),
            ],
        ),
        migrations.AddField(
            model_name='ingredient',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipes', to='ics.Recipe'),
        ),
    ]