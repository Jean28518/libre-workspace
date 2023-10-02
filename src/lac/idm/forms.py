from django import forms


class BasicUserForm(forms.Form):
    username = forms.CharField(label="Benutzername", max_length=100, disabled=True, required=False)
    first_name = forms.CharField(label="Vorname", max_length=100, required=False)
    last_name = forms.CharField(label="Nachname", max_length=100, required=False)
    displayName = forms.CharField(label="Anzeigename", max_length=100, required=False)
    mail = forms.EmailField(label="E-Mail-Adresse", max_length=100, required=False)

class PasswordForm(forms.Form):
    old_password = forms.CharField(label="Altes Passwort", max_length=100, widget=forms.PasswordInput)
    new_password = forms.CharField(label="Neues Passwort", max_length=100, widget=forms.PasswordInput)
    new_password_repeat = forms.CharField(label="Neues Passwort wiederholen", max_length=100, widget=forms.PasswordInput)

class PasswordResetForm(forms.Form):
    email = forms.EmailField(label="E-Mail-Adresse", max_length=100)

class AdministratorUserForm(forms.Form):
    username = forms.CharField(label="Benutzername", max_length=100)
    password = forms.CharField(label="Passwort", max_length=100, widget=forms.PasswordInput)
    first_name = forms.CharField(label="Vorname", max_length=100, required=False)
    last_name = forms.CharField(label="Nachname", max_length=100, required=False)
    mail = forms.EmailField(label="E-Mail-Adresse", max_length=100, required=False)
    admin = forms.BooleanField(label="Administrator", required=False, widget=forms.CheckboxInput)

class AdministratorUserEditForm(forms.Form):
    password = forms.CharField(label="Neues Passwort setzen", max_length=100, widget=forms.PasswordInput, required=False)
    first_name = forms.CharField(label="Vorname", max_length=100, required=False)
    last_name = forms.CharField(label="Nachname", max_length=100, required=False)
    displayName = forms.CharField(label="Anzeigename", max_length=100, required=False)
    mail = forms.EmailField(label="E-Mail-Adresse", max_length=100, required=False)
    admin = forms.BooleanField(label="Administrator", required=False, widget=forms.CheckboxInput)

class GroupCreateForm(forms.Form):
    cn = forms.CharField(label="Gruppenname", max_length=100)
    description = forms.CharField(label="Beschreibung", max_length=100, required=False)
    standard = forms.BooleanField(label="Standardgruppe (Von nun an werden neu erstellte Nutzer dieser Gruppe hinzugefügt)", required=False, widget=forms.CheckboxInput)

class GroupEditForm(forms.Form):
    description = forms.CharField(label="Beschreibung", max_length=100, required=False)
    standard = forms.BooleanField(label="Standardgruppe (Von nun an werden neu erstellte Nutzer dieser Gruppe hinzugefügt)", required=False, widget=forms.CheckboxInput)
