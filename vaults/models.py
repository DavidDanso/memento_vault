# models.py
from django.db import models
from users.models import Profile
import uuid

class Vault(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="vaults")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.title} vault [ {self.owner} ]'
    
    # display new clients first
    class Meta:
        ordering = ['-updated_at']

class VaultMedia(models.Model):
    vault = models.ForeignKey(Vault, on_delete=models.CASCADE, related_name="media_files")
    file = models.FileField(upload_to='vault_media/')  # Supports both images and videos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.vault.title} vault media [ {self.vault.owner} ]'
    
    class Meta:
        ordering = ['-updated_at']
