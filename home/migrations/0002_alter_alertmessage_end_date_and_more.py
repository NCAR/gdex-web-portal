# Generated by Django 4.0.8 on 2025-05-03 18:10

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alertmessage',
            name='end_date',
            field=models.DateField(default=datetime.date(2025, 5, 3), verbose_name='End date'),
        ),
        migrations.AlterField(
            model_name='alertmessage',
            name='start_date',
            field=models.DateField(default=datetime.date(2025, 5, 3), verbose_name='Start date'),
        ),
    ]
