from django import forms
from django.contrib.auth.forms import AuthenticationForm

from apps.users.forms.base import User, widget_css_class


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=100,
        label="",
        label_suffix="",
        help_text="100 characters max.",
        widget=forms.TextInput(
            attrs={
                "class": widget_css_class,
                "placeholder": "",
            }
        ),
    )
    password = forms.CharField(
        label="",
        label_suffix="",
        widget=forms.PasswordInput(
            attrs={
                "class": widget_css_class,
                "placeholder": "............",
            }
        ),
    )

    class Meta:
        model = User
        fields = ["username", "password"]
