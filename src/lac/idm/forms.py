from django import forms
from oidc_provider.models import ResponseType
from django.utils.safestring import mark_safe


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
    admin = forms.BooleanField(label="Administrator (Wenn Nextcloud installiert, dauern dort diese Änderungen einige Minuten)", required=False, widget=forms.CheckboxInput)
    create_linux_user = forms.BooleanField(label=mark_safe("""<b>Für Profis:</b> Zusätzlicher Linux-Benutzer<br>
        <i>(Achtung: Dieser Benutzer wird nur auf dem Linux-Server erstellt. Gruppen werden nicht synchronisiert. Logins auf Linux-Clients sind davon nicht betroffen.)</i>
        """), 
        required=False, widget=forms.CheckboxInput)

class AdministratorUserEditForm(forms.Form):
    guid = forms.CharField(label="objectGUID", max_length=100, disabled=True, required=False)
    password = forms.CharField(label="Neues Passwort setzen", max_length=100, widget=forms.PasswordInput, required=False)
    first_name = forms.CharField(label="Vorname", max_length=100, required=False)
    last_name = forms.CharField(label="Nachname", max_length=100, required=False)
    displayName = forms.CharField(label="Anzeigename", max_length=100, required=False)
    mail = forms.EmailField(label="E-Mail-Adresse", max_length=100, required=False)
    admin = forms.BooleanField(label="Administrator (Wenn Nextcloud installiert, dauern dort diese Änderungen einige Minuten)", required=False, widget=forms.CheckboxInput)
    enabled = forms.BooleanField(label="Aktiviert", required=False, widget=forms.CheckboxInput)

class GroupCreateForm(forms.Form):
    cn = forms.CharField(label="Gruppenname", max_length=100)
    description = forms.CharField(label="Beschreibung", max_length=100, required=False)
    defaultGroup = forms.BooleanField(label="Standardgruppe (Von nun an werden neu erstellte Nutzer dieser Gruppe hinzugefügt)", required=False, widget=forms.CheckboxInput)
    nextcloud_groupfolder = forms.BooleanField(label="Nextcloud-Gruppenordner", required=False, widget=forms.CheckboxInput)

class GroupEditForm(forms.Form):
    description = forms.CharField(label="Beschreibung", max_length=100, required=False)
    defaultGroup = forms.BooleanField(label="Standardgruppe (Von nun an werden neu erstellte Nutzer dieser Gruppe hinzugefügt)", required=False, widget=forms.CheckboxInput)
    nextcloud_groupfolder = forms.BooleanField(label="Nextcloud-Gruppenordner", required=False, widget=forms.CheckboxInput)

class OIDCClientForm(forms.Form):
    name = forms.CharField(label="Name", max_length=100)
    client_type = forms.ChoiceField(label="Client Typ", choices=[("confidential", "Vertraulich"), ("public", "Öffentlich")])
    response_types = forms.ModelMultipleChoiceField(
        queryset=ResponseType.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )
    redirect_uris = forms.CharField(label="Redirect URIs (pro Zeile eine URI eintragen)", widget=forms.Textarea, required=False)    
    client_id = forms.CharField(label="Client ID", max_length=100, required=True)
    client_secret = forms.CharField(label="Client Secret", max_length=100, required=True)
    jwt_alg = forms.ChoiceField(label="JWT Algorithmus", choices=[("RS256", "RS256"), ("HS256", "HS256")])
    require_consent = forms.BooleanField(label="Benutzer muss Datenzugriff zustimmen", required=False, widget=forms.CheckboxInput)
    reuse_consent = forms.BooleanField(label="Konsentierung wiederverwenden", required=False, widget=forms.CheckboxInput)
    
class TOTPChallengeForm(forms.Form):
    # Select Field for the TOTP device
    totp_device = forms.ChoiceField(label="TOTP Gerät", choices=[], required=False)
    # Input Field for the TOTP token
    totp_code = forms.CharField(label="TOTP-Code (Sechsstellig)", max_length=100, required=False)