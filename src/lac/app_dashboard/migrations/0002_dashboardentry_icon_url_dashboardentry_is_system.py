# Generated by Django 5.0.1 on 2024-02-03 20:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_dashboard', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dashboardentry',
            name='icon_url',
            field=models.CharField(default='', max_length=1000),
        ),
        migrations.AddField(
            model_name='dashboardentry',
            name='is_system',
            field=models.BooleanField(default=False),
        ),
    ]
