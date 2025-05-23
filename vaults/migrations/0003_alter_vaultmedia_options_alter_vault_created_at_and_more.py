# Generated by Django 5.1.1 on 2025-04-07 14:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx'),
        ('users', '0001_initial'),
        ('vaults', '0002_alter_vault_id'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='vaultmedia',
            options={},
        ),
        migrations.AlterField(
            model_name='vault',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='vault',
            name='title',
            field=models.CharField(db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='vault',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='vaultmedia',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
        migrations.AddIndex(
            model_name='vault',
            index=models.Index(fields=['-updated_at'], name='vaults_vaul_updated_7dc9a7_idx'),
        ),
        migrations.AddIndex(
            model_name='vault',
            index=models.Index(fields=['owner', '-updated_at'], name='vaults_vaul_owner_i_4c5104_idx'),
        ),
        migrations.AddIndex(
            model_name='vaultmedia',
            index=models.Index(fields=['vault', '-updated_at'], name='vaults_vaul_vault_i_24f77a_idx'),
        ),
    ]
