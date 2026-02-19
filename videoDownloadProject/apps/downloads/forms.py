from django import forms


class FetchMetadataForm(forms.Form):
    video_url = forms.URLField(
        label="Video URL",
        max_length=500,
        required=True,
        widget=forms.URLInput(
            attrs={
                "type": "text",
                "class": "input",
                "placeholder": "https://video.example.com/watch?v=...",
            }
        ),
    )

