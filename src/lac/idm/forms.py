from django import forms


class BasicUserForm(forms.Form):
    username = forms.CharField(label="Benutzername", max_length=100, disabled=True, required=False)
    first_name = forms.CharField(label="Vorname", max_length=100)
    last_name = forms.CharField(label="Nachname", max_length=100)
    cn = forms.CharField(label="Anzeigename", max_length=100)
    mail = forms.EmailField(label="E-Mail-Adresse", max_length=100)

class PasswordForm(forms.Form):
    old_password = forms.CharField(label="Altes Passwort", max_length=100, widget=forms.PasswordInput)
    new_password = forms.CharField(label="Neues Passwort", max_length=100, widget=forms.PasswordInput)
    new_password_repeat = forms.CharField(label="Neues Passwort wiederholen", max_length=100, widget=forms.PasswordInput)

class PasswordResetForm(forms.Form):
    email = forms.EmailField(label="E-Mail-Adresse", max_length=100)