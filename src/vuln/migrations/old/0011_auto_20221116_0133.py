# Generated by Django 3.2.16 on 2022-11-16 01:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vuln', '0010_auto_20221114_0705'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='content',
            name='sv_pkg',
        ),
        migrations.AddField(
            model_name='content',
            name='id',
            field=models.BigIntegerField(default=1, primary_key=True, serialize=False),
            preserve_default=False,
        ),
    ]
