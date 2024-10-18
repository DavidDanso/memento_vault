from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from users.models import *

# User Registration form
class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        
        # add id and placeholder to the input field
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'what others will see'}),
            'email': forms.TextInput(attrs={'placeholder': 'enter your email'})
        }
    # add class to the input field
    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        for name, fields in self.fields.items():
            fields.widget.attrs.update({'class': 'form-control form-control-lg input'})

# User Profile form
class UserProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = '__all__'
        exclude = ['user']
    # add class to the input field
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for name, fields in self.fields.items():
            fields.widget.attrs.update({'class': 'form-control form-control-lg input'})