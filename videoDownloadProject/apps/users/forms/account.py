from django import forms
from django.contrib.auth.forms import UserCreationForm

from apps.users.forms.base import User, widget_css_class


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
