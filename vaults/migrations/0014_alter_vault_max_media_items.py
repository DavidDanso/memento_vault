# Generated by Django 5.1.1 on 2024-12-19 18:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vaults', '0013_remove_vault_guest_num_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vault',
            name='max_media_items',
            field=models.PositiveIntegerField(default=2),
        ),
    ]