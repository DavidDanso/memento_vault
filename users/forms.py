from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['displayname', 'image', 'username', 'email', 'location']
        widgets = {
            'image': forms.FileInput(),
            'displayname': forms.TextInput(attrs={'placeholder': 'Add display name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email address'}),
            'location': forms.TextInput(attrs={'placeholder': 'Enter your location'}),
        }
        exclude = ['user']

    # add class to the input field
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        for name, fields in self.fields.items():
            fields.widget.attrs.update({'class': 'form-control form-control-lg input'})
        


# User Registration form
class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        # add id and placeholder to the input field
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'what others will see'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email address'}),
        }
    # add class to the input field
    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        for name, fields in self.fields.items():
            fields.widget.attrs.update({'class': 'form-control form-control-lg input'})