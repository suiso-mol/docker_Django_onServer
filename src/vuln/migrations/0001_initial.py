# Generated by Django 3.2.16 on 2022-12-08 06:11

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Package',
            fields=[
                ('pkg_name', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('architecture', models.CharField(blank=True, max_length=50)),
                ('description', models.CharField(blank=True, max_length=100)),
                ('remark', models.CharField(blank=True, max_length=200)),
                ('update_date', models.DateTimeField(auto_now=True)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Server',
            fields=[
                ('sv_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('ip', models.GenericIPAddressField()),
                ('os', models.CharField(max_length=100)),
                ('usage', models.CharField(blank=True, max_length=200)),
                ('remark', models.CharField(blank=True, max_length=200)),
                ('update_date', models.DateTimeField(auto_now=True)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Content',
            fields=[
                ('sv_pkg', models.SlugField(max_length=150, primary_key=True, serialize=False, unique=True)),
                ('version', models.CharField(max_length=50)),
                ('update_date', models.DateTimeField(auto_now=True)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('pkg_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vuln.package')),
                ('sv_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vuln.server')),
            ],
        ),
    ]
