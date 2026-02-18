from django import forms
from django.contrib.auth.forms import PasswordChangeForm

from apps.users.forms.base import widget_css_class


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
