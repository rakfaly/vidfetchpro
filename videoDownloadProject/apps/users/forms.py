from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=100,
        label="",
        label_suffix="",
        help_text="100 characters max.",
        widget=forms.TextInput(
            attrs={
                "class": "w-full bg-gray-800/50 border border-gray-700 rounded-lg py-3 pl-10 pr-4 "
                "focus:outline-none focus:border-brand transition",
                "placeholder": "",
            }
        ),
    )
    password = forms.CharField(
        label="",
        label_suffix="",
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full bg-gray-800/50 border border-gray-700 rounded-lg py-3 pl-10 pr-4 focus:outline-none "
                "focus:border-brand transition",
                "placeholder": "............",
            }
        ),
    )

    class Meta:
        model = User
        fields = ["username", "password"]
