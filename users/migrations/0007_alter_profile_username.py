# Generated by Django 5.1.1 on 2024-10-30 02:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_profile_username_alter_profile_displayname_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='username',
            field=models.CharField(default='john_doe', max_length=20, unique=True),
        ),
    ]
