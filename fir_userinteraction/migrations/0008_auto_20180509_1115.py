# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-09 11:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fir_userinteraction', '0007_auto_20180418_1727'),
    ]

    operations = [
        migrations.AddField(
            model_name='questiongroup',
            name='label',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='questiongroup',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='questiongroup',
            name='title',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
