# Generated by Django 5.1.1 on 2025-04-08 10:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx'),
        ('users', '0001_initial'),
        ('vaults', '0004_rename_max_media_items_vault_uploads_per_person'),
    ]

    operations = [
        migrations.AddField(
            model_name='vaultmedia',
            name='uploader_profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploaded_media', to='users.profile'),
        ),
        migrations.AddField(
            model_name='vaultmedia',
            name='uploader_session_key',
            field=models.CharField(blank=True, db_index=True, max_length=40, null=True),
        ),
        migrations.AddIndex(
            model_name='vaultmedia',
            index=models.Index(fields=['vault', 'uploader_profile'], name='vaults_vaul_vault_i_6aa5f0_idx'),
        ),
        migrations.AddIndex(
            model_name='vaultmedia',
            index=models.Index(fields=['vault', 'uploader_session_key'], name='vaults_vaul_vault_i_68dc9c_idx'),
        ),
    ]
