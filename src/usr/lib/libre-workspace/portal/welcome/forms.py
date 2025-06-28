from django import forms
from django.utils.translation import gettext_lazy as _

from django.conf import settings

class LanguageSelectionForm(forms.Form):
    language_code = forms.ChoiceField(
        label=_("Select Language"),
        choices=[(lang) for lang in settings.LANGUAGES],
        initial='en',
        widget=forms.Select(attrs={'class': 'form-control'})
    )