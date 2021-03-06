# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-18 17:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('incidents', '0010_auto_20170122_1208'),
        ('fir_userinteraction', '0006_questiongroup_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='AutoNotifyDuration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('duration', models.DurationField()),
                ('severity', models.IntegerField(choices=[(1, b'1'), (2, b'2'), (3, b'3'), (4, b'4')])),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='incidents.IncidentCategory')),
            ],
        ),
        migrations.RemoveField(
            model_name='quizwatchlistitem',
            name='email',
        ),
        migrations.AddField(
            model_name='quizwatchlistitem',
            name='business_line',
            field=models.ForeignKey(blank=True, help_text='Business Line for the watchlist', null=True, on_delete=django.db.models.deletion.CASCADE, to='incidents.BusinessLine'),
        ),
        migrations.AlterField(
            model_name='quizwatchlistitem',
            name='quiz',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='fir_userinteraction.Quiz'),
        ),
    ]
