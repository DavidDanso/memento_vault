# models.py
from django.db import models
from users.models import Profile
import uuid
from django.utils import timezone
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator

class Vault(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="vaults")
    guest_num = models.IntegerField(default=2, null=True, blank=True, validators=[
            MinValueValidator(2),
            MaxValueValidator(10)
        ])
    photos_per_person = models.IntegerField(default=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.title} vault [ {self.owner} ]'
    
    # display new vaults first
    class Meta:
        ordering = ['-updated_at']

class VaultMedia(models.Model):
    vault = models.ForeignKey(Vault, on_delete=models.CASCADE, related_name="media_files")
    file = models.FileField(upload_to='vault_media/')  # Supports both images and videos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    #
    def save(self, *args, **kwargs):
        # Save the media instance
        super().save(*args, **kwargs)
        # Update the parent vault's timestamp
        self.vault.updated_at = timezone.now()
        self.vault.save()

    def __str__(self):
        return f'{self.vault.title} vault media [ {self.vault.owner} ]'

    class Meta:
        ordering = ['-updated_at']


# Signal to update the Vault's updated_at field when a VaultMedia instance is deleted
@receiver(post_delete, sender=VaultMedia)
def update_vault_on_media_delete(sender, instance, **kwargs):
    vault = instance.vault
    vault.updated_at = timezone.now()
    vault.save()
