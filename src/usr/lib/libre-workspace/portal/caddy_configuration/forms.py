from django import forms
from django.utils.translation import gettext as _

class CaddyConfigurationEntryForm(forms.Form):
    name = forms.CharField(label=_("Name"), max_length=255, required=True)
    block = forms.CharField(label=_("Block"), widget=forms.Textarea, required=True)


class CaddyReverseProxyForm(forms.Form):
    name = forms.CharField(label=_("Name"), max_length=255, required=True)
    domain = forms.CharField(label=_("Domain"), max_length=255, required=True, widget=forms.TextInput(attrs={'placeholder': _('myservice.int.de')}))
    port = forms.IntegerField(label=_("Port (Optional)"), required=False, min_value=1, max_value=65535, widget=forms.TextInput(attrs={'placeholder': _('(Optional)')}))
    internal_https = forms.BooleanField(label=_("Internal HTTPS (for local instances)"), required=False, initial=False)
    target_url = forms.CharField(label=_("Target URL"), max_length=255, required=True, initial="http://localhost:8000")