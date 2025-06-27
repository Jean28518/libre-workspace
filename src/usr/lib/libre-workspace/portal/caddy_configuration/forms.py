from django import forms

class CaddyConfigurationEntryForm(forms.Form):
    name = forms.CharField(label="Name", max_length=255, required=True)
    block = forms.CharField(label="Block", widget=forms.Textarea, required=True)


class CaddyReverseProxyForm(forms.Form):
    name = forms.CharField(label="Name", max_length=255, required=True)
    domain = forms.CharField(label="Domain", max_length=255, required=True, widget=forms.TextInput(attrs={'placeholder': 'myservice.int.de'}))
    port = forms.IntegerField(label="Port (Optional)", required=False, min_value=1, max_value=65535, widget=forms.TextInput(attrs={'placeholder': '(Optional)'}))
    internal_https = forms.BooleanField(label="Internal HTTPS (for local instances)", required=False, initial=False)
    target_url = forms.CharField(label="Target URL", max_length=255, required=True, initial="http://localhost:8000")