# Generated by Django 3.2.16 on 2022-11-04 06:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vuln', '0002_server_ip'),
    ]

    operations = [
        migrations.AlterField(
            model_name='package',
            name='architecture',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='package',
            name='description',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='package',
            name='remark',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='server',
            name='remark',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='server',
            name='usage',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
