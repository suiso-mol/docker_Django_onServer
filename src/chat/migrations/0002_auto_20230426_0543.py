# Generated by Django 3.2.18 on 2023-04-26 05:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatlog',
            name='check',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='chatlog',
            name='relation_id',
            field=models.IntegerField(default=0),
        ),
    ]
