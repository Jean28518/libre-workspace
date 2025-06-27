from django import forms

class WordpressInstanceForm(forms.Form):
    name = forms.CharField(label="Name", max_length=255, required=True)
    domain = forms.CharField(label="Domain", max_length=255, required=True, widget=forms.TextInput(attrs={'placeholder': 'mysite.int.de'}))
    admin_password = forms.CharField(
        label="Administrator password for the WordPress instance",
        max_length=255,
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'User will be named "Administrator"'}),
    )
    admin_email = forms.EmailField(
        label="Administrator email for the WordPress instance",
        max_length=255,
        required=True,
    )
    locale = forms.CharField(
        label="Locale for the WordPress instance. German would be 'de_DE'.",
        max_length=10,
        required=False,
        initial="en_US",
    )
    