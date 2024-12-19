# forms.py
from django import forms
from .models import Vault, VaultMedia

class VaultCreationForm(forms.ModelForm):
    class Meta:
        model = Vault
        fields = ['title', 'max_media_items']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'name your new vault...'}),
            'max_media_items': forms.NumberInput(attrs={'placeholder': 'enter max media items (2-15)...',
                                                        'min': 2, 'max': 15, 'step': 1,}),
        }

    def __init__(self, *args, **kwargs):
        super(VaultCreationForm, self).__init__(*args, **kwargs)
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
            
