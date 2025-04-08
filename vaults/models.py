# models.py
from django.db import models
import qrcode
from django.core.files.base import ContentFile
from io import BytesIO
from users.models import Profile # Assuming 'Profile' is your effective user identifier model
import uuid
from django.utils import timezone
from django.db.models.signals import post_delete
from django.dispatch import receiver
from taggit.managers import TaggableManager
from django.conf import settings # For referencing the User model if needed

class Vault(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100, db_index=True)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="vaults")
    # The maximum number of uploads allowed per individual user/session
    uploads_per_person = models.PositiveIntegerField(default=2)
    qr_code = models.ImageField(upload_to='vault_qrcodes/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    def __str__(self):
        return f'{self.title} vault [ {self.owner} ]'

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
            models.Index(fields=['owner', '-updated_at']),
        ]

    def generate_qr_code(self):
        if self.qr_code:
            return
        upload_url = f"http://127.0.0.1:8000/user-uploads/{self.id}" # Placeholder

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(upload_url)
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        filename = f"vault_{self.id}.png"
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)

    # Method to save the model and generate QR if needed
    def save(self, *args, **kwargs):
        if not self.pk: # Only generate QR on initial creation if needed
             self.generate_qr_code()
        super().save(*args, **kwargs)


class VaultMedia(models.Model):
    vault = models.ForeignKey(Vault, on_delete=models.CASCADE, related_name="media_files")
    file = models.FileField(upload_to='vault_media/')
    caption = models.TextField(blank=True, null=True)
    tags = TaggableManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    # Link to the logged-in user's Profile who uploaded this
    uploader_profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='uploaded_media'
    )
    # Store the session key for anonymous users who uploaded this
    uploader_session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding # Check if this is a new instance
        super().save(*args, **kwargs)
        # Update the parent vault's timestamp only if it's a new upload
        if is_new:
            self.vault.updated_at = timezone.now()
            self.vault.save(update_fields=['updated_at'])

    def __str__(self):
        uploader_info = f"by {self.uploader_profile}" if self.uploader_profile else f"by session {self.uploader_session_key[:8]}..." if self.uploader_session_key else "by unknown"
        return f'{self.vault.title} media {uploader_info}'

    class Meta:
        indexes = [
            models.Index(fields=['vault', '-updated_at']),
            # Index for efficiently counting uploads per user/session within a vault
            models.Index(fields=['vault', 'uploader_profile']),
            models.Index(fields=['vault', 'uploader_session_key']),
        ]

# Signal to update the Vault's updated_at field when a VaultMedia instance is deleted
@receiver(post_delete, sender=VaultMedia)
def update_vault_on_media_delete(sender, instance, **kwargs):
    try:
        vault = instance.vault
        # Check if vault still exists before trying to update
        if vault:
            vault.updated_at = timezone.now()
            vault.save(update_fields=['updated_at'])
    except Vault.DoesNotExist:
        # Handle case where the vault might have been deleted already
        pass