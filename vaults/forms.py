# forms.py
from django import forms
from .models import Vault, VaultMedia
from django.core.validators import MinValueValidator, MaxValueValidator

class VaultCreationForm(forms.ModelForm):
    class Meta:
        model = Vault
        fields = ['title', 'uploads_per_person', 'qr_code_active_days']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'name your new vault...'}),
            'uploads_per_person': forms.NumberInput(attrs={'placeholder': 'enter max media items (2-25)...',
                                                        'min': 2, 'max': 25, 'step': 1,}),
            'qr_code_active_days': forms.NumberInput(attrs={'placeholder': 'enter QR code active minutes...',
                                                              'min': 1, 'max': 4, 'step': 1}),
        }

    def __init__(self, *args, **kwargs):
        super(VaultCreationForm, self).__init__(*args, **kwargs)
        # Override any default validators with our custom range
        self.fields['qr_code_active_days'].validators = [
            MinValueValidator(2),
            MaxValueValidator(5760)
        ]
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input form-control'})


class VaultMediaForm(forms.ModelForm):
    class Meta:
        model = VaultMedia
        fields = ['file']  # Only the file field for uploading media

    # Custom method to handle multiple file uploads
    def clean_file(self):
        files = self.cleaned_data.get('file')
        if not files:
            raise forms.ValidationError("No files were uploaded.")
        return files
            
