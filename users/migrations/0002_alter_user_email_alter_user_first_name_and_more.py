# Generated by Django 4.2.11 on 2024-03-30 17:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.CharField(max_length=256, unique=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="first_name",
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name="user",
            name="last_name",
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name="user",
            name="username",
            field=models.CharField(max_length=128, unique=True),
        ),
    ]
