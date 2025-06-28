from django import forms
from django.utils.translation import gettext as _

class WordpressInstanceForm(forms.Form):
    name = forms.CharField(label=_("Name"), max_length=255, required=True)
    domain = forms.CharField(label=_("Domain"), max_length=255, required=True, widget=forms.TextInput(attrs={'placeholder': 'mysite.int.de'}))
    # admin_password = forms.CharField(
    #     label=_("Administrator password for the WordPress instance"),
    #     max_length=255,
    #     required=True,
    #     widget=forms.PasswordInput(attrs={'placeholder': _('User will be named "Administrator"')}),
    # )
    # admin_email = forms.EmailField(
    #     label=_("Administrator email for the WordPress instance"),
    #     max_length=255,
    #     required=True,
    # )
    # locale = forms.CharField(
    #     label=_("Locale for the WordPress instance. German would be 'de_DE'."),
    #     max_length=10,
    #     required=False,
    #     initial="en_US",
    # )