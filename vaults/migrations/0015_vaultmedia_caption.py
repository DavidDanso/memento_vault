# Generated by Django 5.1.1 on 2025-01-01 18:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vaults', '0014_alter_vault_max_media_items'),
    ]

    operations = [
        migrations.AddField(
            model_name='vaultmedia',
            name='caption',
            field=models.TextField(blank=True, null=True),
        ),
    ]