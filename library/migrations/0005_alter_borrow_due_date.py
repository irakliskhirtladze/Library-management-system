# Generated by Django 5.0.4 on 2024-05-18 08:55

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0004_alter_borrow_due_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='borrow',
            name='due_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 6, 1, 8, 55, 44, 113982, tzinfo=datetime.timezone.utc)),
        ),
    ]