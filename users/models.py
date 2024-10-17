from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import uuid

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='avatars/', null=True, blank=True)
    displayname = models.CharField(max_length=20, null=True, blank=True)
    username = models.CharField(max_length=20, null=True, blank=True)
    location = models.CharField(max_length=20, null=True, blank=True) 
    email = models.EmailField(max_length=255, unique=True, blank=True, default="noemail@domain.com")
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    
    def __str__(self):
        return self.name or str(self.user)
    
    @property
    def name(self):
        return self.displayname or self.username or self.user.username
    
    @property
    def avatar(self):
        # If the user has uploaded an image, return the image URL
        if self.image:
            return self.image.url
        # Otherwise, return the path to the default avatar
        return f'{settings.STATIC_URL}images/default-avatar.png'