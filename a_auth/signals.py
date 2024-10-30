# signals.py
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from users.models import Profile

# Automatically create a Profile when a User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(
            user=instance,
            username=instance.username,
            email=instance.email,
        )

# Automatically update User's email and username when Profile is updated
@receiver(post_save, sender=Profile)
def update_user_from_profile(sender, instance, created, **kwargs):
    if not created:
        user = instance.user
        if user.email != instance.email or user.username != instance.username:
            user.email = instance.email
            user.username = instance.username
            user.save()

# Automatically delete the User when a Profile is deleted
@receiver(post_delete, sender=Profile)
def delete_user_on_profile_delete(sender, instance, **kwargs):
    user = instance.user
    user.delete()
