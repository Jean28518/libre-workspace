from django import forms


class BackupSettings(forms.Form):
    enabled = forms.BooleanField(label="Automatische Backups aktivieren", required=False, widget=forms.CheckboxInput(attrs={"role": "switch"}), help_text = "\n")
    borg_repository = forms.CharField(label="Borg Repository", max_length=100, widget=forms.TextInput(attrs={"placeholder": "ssh://user@1.2.3.4:22/~/backups/Server1"}))
    trusted_fingerprint = forms.CharField(label="Fingerabdruck des SSH-Zugangs. (Siehe wichtige Hinweise)", widget=forms.Textarea())
    borg_encryption = forms.BooleanField(label="Borg Verschlüsselung", required=False, widget=forms.CheckboxInput(attrs={"role": "switch"}), help_text = "\n")
    borg_passphrase = forms.CharField(label="Borg Passphrase (nur bei aktivierter Verschlüsselung auszufüllen)", max_length=100, required=False)
    daily_backup_time = forms.CharField(label="Tägliche Backupzeit (Format: HH:MM)", max_length=100, widget=forms.TextInput(attrs={"placeholder": "02:00"}))
    keep_daily_backups = forms.IntegerField(label="Anzahl der täglichen Backups", min_value=0, max_value=100, widget=forms.NumberInput(attrs={"placeholder": "7"}))
    keep_weekly_backups = forms.IntegerField(label="Anzahl der wöchentlichen Backups", min_value=0, max_value=100, widget=forms.NumberInput(attrs={"placeholder": "6"}))
    keep_monthly_backups = forms.IntegerField(label="Anzahl der monatlichen Backups", min_value=0, max_value=100, widget=forms.NumberInput(attrs={"placeholder": "12"}))
    borg_repo_is_on_synology = forms.BooleanField(label="Borg Repository ist auf einem Synology NAS", required=False, widget=forms.CheckboxInput(attrs={"role": "switch"}), help_text = "\n")
    additional_borg_options = forms.CharField(label="Zusätzliche Borg Optionen (für Experten)", max_length=1000, required=False, widget=forms.TextInput())


class EmailConfiguration(forms.Form):
    server = forms.CharField(label="E-Mail Server", max_length=100, widget=forms.TextInput(attrs={"placeholder": "mail.example.com"}))
    port = forms.IntegerField(label="E-Mail Port", min_value=0, max_value=10000, widget=forms.NumberInput(attrs={"placeholder": "587"}))
    user = forms.CharField(label="E-Mail Benutzername", max_length=100, widget=forms.TextInput(attrs={"placeholder": "example@example.com"}))
    email = forms.EmailField(label="E-Mail Adresse", max_length=100, widget=forms.EmailInput(attrs={"placeholder": "example@example.com"}))
    password = forms.CharField(label="E-Mail Passwort", max_length=100, widget=forms.PasswordInput(attrs={"placeholder": "Passwort"}),  required=False)
    encryption = forms.ChoiceField(label="E-Mail Verschlüsselung", choices=[("TLS", "TLS"), ("SSL", "SSL")], widget=forms.Select(attrs={"class": "form-control"}))
                                                                                                            

class OnlineOfficeInstallationForm(forms.Form):
    # Selection between OnlyOffice and Collabora and nothing
    online_office = forms.ChoiceField(label="Online Office", choices=[("Collabora", "Collabora"), ("OnlyOffice", "OnlyOffice"), ("Deaktivieren", "Deaktivieren")], widget=forms.Select(attrs={"class": "form-control"}))


class AddonForm(forms.Form):
    file = forms.FileField(label="Add-On Datei")


class ChangeLibreWorkspaceNameForm(forms.Form):
    name = forms.CharField(label="Neuer Libre-Workspace Name", max_length=100, widget=forms.TextInput(), required=False)


class ChangeIpAdressForm(forms.Form):
    ip = forms.GenericIPAddressField(label="IP-Adresse", widget=forms.TextInput(attrs={"placeholder": "0.0.0.0"}))


class MiscellaneousSettingsForm(forms.Form):
    additional_mail_addresses_for_system_mails = forms.CharField(label="Zusätzliche E-Mail-Adressen für System-E-Mails (bei mehreren mit Komma trennen)", max_length=100, widget=forms.TextInput(), required=False)
    disable_nextcloud_user_administration = forms.BooleanField(label="Nextcloud Benutzerverwaltung deaktivieren", required=False, widget=forms.CheckboxInput(attrs={"role": "switch"}), help_text = "\n")
    cpu_warning_threshold = forms.IntegerField(label="CPU Warnschwelle in %", min_value=0, max_value=100, widget=forms.NumberInput(attrs={"placeholder": "80"}))
    ram_warning_threshold = forms.IntegerField(label="RAM Warnschwelle in %", min_value=0, max_value=100, widget=forms.NumberInput(attrs={"placeholder": "80"}))
    disk_warning_threshold = forms.IntegerField(label="Festplatten Warnschwelle in %", min_value=0, max_value=100, widget=forms.NumberInput(attrs={"placeholder": "90"}))


class AdditionalServicesForm(forms.Form):
    start_additional_services = forms.CharField(label="Startbefehl der zusätzlichen Dienste (Bash-Code)", widget=forms.Textarea(), required=False)
    stop_additional_services = forms.CharField(label="Stopbefehl der zusätzlichen Dienste (Bash-Code)", widget=forms.Textarea(), required=False)


class AutomaticShutdownForm(forms.Form):
    enabled = forms.BooleanField(label="Automatisches Neustarten/Herunterfahren aktivieren", required=False, widget=forms.CheckboxInput(attrs={"role": "switch"}), help_text = "\n")
    type = forms.ChoiceField(label="Aktion", choices=[("Reboot", "Neustart"), ("Shutdown", "Herunterfahren")], widget=forms.Select(attrs={"class": "form-control"}))
    time = forms.CharField(label="Uhrzeit (Format: HH:MM)", max_length=100, widget=forms.TextInput())
    weekday = forms.ChoiceField(label="Wochentag", choices=[("daily", "Täglich"), ("0", "Montag"), ("1", "Dienstag"), ("2", "Mittwoch"), ("3", "Donnerstag"), ("4", "Freitag"), ("5", "Samstag"), ("6", "Sonntag")], widget=forms.Select(attrs={"class": "form-control"}))


class DesktopSettingsForm(forms.Form):
    set_desktop_password = forms.CharField(label="Desktop Passwort setzen", max_length=100, widget=forms.PasswordInput(attrs={"placeholder": "Passwort"}), required=False)