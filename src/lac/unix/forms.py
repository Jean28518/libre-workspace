from django import forms


class BackupSettings(forms.Form):
    enabled = forms.BooleanField(label="Automatische Backups aktivieren", required=False, widget=forms.CheckboxInput(attrs={"role": "switch"}), help_text = "\n")
    borg_repository = forms.CharField(label="Borg Repository", max_length=100, widget=forms.TextInput(attrs={"placeholder": "ssh://borg@1.2.3.4:22/~/backups/Server1"}))
    trusted_fingerprint = forms.CharField(label="Fingerabdruck des SSH-Zugangs. (Siehe wichtige Hinweise)", widget=forms.Textarea())
    borg_encryption = forms.BooleanField(label="Borg Verschlüsselung", required=False, widget=forms.CheckboxInput(attrs={"role": "switch"}), help_text = "\n")
    borg_passphrase = forms.CharField(label="Borg Passphrase (nur bei aktivierter Verschlüsselung auszufüllen)", max_length=100, required=False)
    daily_backup_time = forms.CharField(label="Tägliche Backupzeit (Format: HH:MM)", max_length=100, widget=forms.TextInput(attrs={"placeholder": "02:00"}))
    keep_daily_backups = forms.IntegerField(label="Anzahl der täglichen Backups", min_value=0, max_value=100, widget=forms.NumberInput(attrs={"placeholder": "7"}))
    keep_weekly_backups = forms.IntegerField(label="Anzahl der wöchentlichen Backups", min_value=0, max_value=100, widget=forms.NumberInput(attrs={"placeholder": "6"}))
    keep_monthly_backups = forms.IntegerField(label="Anzahl der monatlichen Backups", min_value=0, max_value=100, widget=forms.NumberInput(attrs={"placeholder": "12"}))
    borg_repo_is_on_synology = forms.BooleanField(label="Borg Repository ist auf einem Synology NAS", required=False, widget=forms.CheckboxInput(attrs={"role": "switch"}), help_text = "\n")


class EmailConfiguration(forms.Form):
    server = forms.CharField(label="E-Mail Server", max_length=100, widget=forms.TextInput(attrs={"placeholder": "mail.example.com"}))
    port = forms.IntegerField(label="E-Mail Port", min_value=0, max_value=10000, widget=forms.NumberInput(attrs={"placeholder": "587"}))
    user = forms.CharField(label="E-Mail Benutzername", max_length=100, widget=forms.TextInput(attrs={"placeholder": "example@example.com"}))
    password = forms.CharField(label="E-Mail Passwort", max_length=100, widget=forms.PasswordInput(attrs={"placeholder": "Passwort"}),  required=False)
    encryption = forms.ChoiceField(label="E-Mail Verschlüsselung", choices=[("TLS", "TLS"), ("SSL", "SSL")], widget=forms.Select(attrs={"class": "form-control"}))
                                                                                                            

class OnlineOfficeInstallationForm(forms.Form):
    # Selection between OnlyOffice and Collabora and nothing
    online_office = forms.ChoiceField(label="Online Office", choices=[("Collabora", "Collabora"), ("OnlyOffice", "OnlyOffice"), ("Deaktivieren", "Deaktivieren")], widget=forms.Select(attrs={"class": "form-control"}))