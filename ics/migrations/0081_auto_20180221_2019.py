# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-21 20:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ics', '0080_invitecode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attribute',
            name='datatype',
            field=models.CharField(choices=[(b'TEXT', b'text data'), (b'NUMB', b'number data'), (b'DATE', b'date data'), (b'TIME', b'time data'), (b'USER', b'user data')], default=b'TEXT', max_length=4),
        ),
        migrations.AlterField(
            model_name='processtype',
            name='description',
            field=models.CharField(default='', max_length=200),
        ),
        migrations.AlterField(
            model_name='processtype',
            name='name',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='processtype',
            name='output_desc',
            field=models.CharField(default='product', max_length=200),
        ),
        migrations.AlterField(
            model_name='producttype',
            name='description',
            field=models.CharField(default='', max_length=200),
        ),
        migrations.AlterField(
            model_name='producttype',
            name='name',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='task',
            name='custom_display',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='task',
            name='label',
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='taskattribute',
            name='value',
            field=models.CharField(blank=True, max_length=104),
        ),
        migrations.AlterField(
            model_name='taskformulaattribute',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='formula_attributes', to='ics.Task'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='walkthrough',
            field=models.IntegerField(default=1),
        ),
    ]
