# custom_filters.py
from django import template
import os

register = template.Library()

@register.filter
def truncate_filename(value, length=20):
    # Remove the "vault_media/" prefix
    filename = value.replace("vault_media/", "")
    # Split into name and extension
    base, ext = os.path.splitext(filename)
    # Truncate the base name and add the extension back
    if len(base) > length:
        base = base[:length] + ''
    return f"{base}{ext}"
