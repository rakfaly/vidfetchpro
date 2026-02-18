from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
)
from django.contrib.auth.models import User

widget_css_class = """w-full bg-gray-800/50 border border-gray-700 rounded-lg
        py-3 pl-10 pr-4 focus:outline-none focus:border-brand transition"""


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


class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(
        label="",
        label_suffix="",
        widget=forms.PasswordInput(
            attrs={
                "class": widget_css_class,
                "placeholder": "............",
            }
        ),
    )
    password2 = forms.CharField(
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
        fields = ["first_name", "last_name", "email", "username"]
        widgets = {
            "username": forms.TextInput(attrs={"class": widget_css_class}),
            "email": forms.TextInput(
                attrs={"class": widget_css_class, "placeholder": "name@example.com"}
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": widget_css_class,
                    "autofocus": "autofocus",
                }
            ),
            "last_name": forms.TextInput(attrs={"class": widget_css_class}),
        }


class CustomUserUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "username"]
        widgets = {
            "username": forms.TextInput(attrs={"class": widget_css_class}),
            "email": forms.TextInput(
                attrs={"class": widget_css_class, "placeholder": "name@example.com"}
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": widget_css_class,
                }
            ),
            "last_name": forms.TextInput(attrs={"class": widget_css_class}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="",
        label_suffix="",
        widget=forms.PasswordInput(
            attrs={
                "class": widget_css_class,
                "placeholder": "Current password",
            }
        ),
    )
    new_password1 = forms.CharField(
        label="",
        label_suffix="",
        widget=forms.PasswordInput(
            attrs={
                "class": widget_css_class,
                "placeholder": "New password",
            }
        ),
    )
    new_password2 = forms.CharField(
        label="",
        label_suffix="",
        widget=forms.PasswordInput(
            attrs={
                "class": widget_css_class,
                "placeholder": "Confirm new password",
            }
        ),
    )
