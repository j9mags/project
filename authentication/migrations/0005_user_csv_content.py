# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-23 14:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_auto_20170731_0930'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='csv_content',
            field=models.TextField(blank=True, null=True),
        ),
    ]
