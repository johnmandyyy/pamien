# Generated by Django 4.1.4 on 2023-10-07 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='live',
            name='description',
            field=models.CharField(max_length=150),
        ),
        migrations.AlterField(
            model_name='live',
            name='title',
            field=models.CharField(max_length=70),
        ),
    ]
