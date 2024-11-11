# forms.py
from django import forms
from .models import Vault, VaultMedia

class VaultCreationForm(forms.ModelForm):
    class Meta:
        model = Vault
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'name your new vault...'}),
        }

    def __init__(self, *args, **kwargs):
        super(VaultCreationForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input form-control'})

class VaultMediaForm(forms.ModelForm):
    class Meta:
        model = VaultMedia
        fields = ['file']  # Only the file field for uploading media

    def __init__(self, *args, **kwargs):
        super(VaultMediaForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input form-control'})
