# Generated by Django 5.1.1 on 2024-10-30 13:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vaults', '0002_alter_vault_owner'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vault',
            name='content',
        ),
        migrations.CreateModel(
            name='VaultMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.ImageField(upload_to='vault_media/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('vault', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='media_files', to='vaults.vault')),
            ],
        ),
    ]