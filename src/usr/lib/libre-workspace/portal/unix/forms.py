from django import forms
from django.utils.translation import gettext as _


class BackupSettings(forms.Form):
    enabled = forms.BooleanField(label=_("Enable automatic backups"), required=False, widget=forms.CheckboxInput(attrs={"role": "switch"}), help_text = "\n")
    borg_repository = forms.CharField(label=_("Borg Repository"), max_length=100, widget=forms.TextInput(attrs={"placeholder": "ssh://user@1.2.3.4:22/~/backups/Server1"}))
    trusted_fingerprint = forms.CharField(label=_("SSH access fingerprint (See important notes)"), widget=forms.Textarea())
    borg_encryption = forms.BooleanField(label=_("Borg Encryption"), required=False, widget=forms.CheckboxInput(attrs={"role": "switch"}), help_text = "\n")
    borg_passphrase = forms.CharField(label=_("Borg Passphrase (only fill if encryption is enabled)"), max_length=100, required=False)
    daily_backup_time = forms.CharField(label=_("Daily backup time (Format: HH:MM)"), max_length=100, widget=forms.TextInput(attrs={"placeholder": "02:00"}))
    keep_daily_backups = forms.IntegerField(label=_("Number of daily backups"), min_value=0, max_value=1000, widget=forms.NumberInput(attrs={"placeholder": "7"}))
    keep_weekly_backups = forms.IntegerField(label=_("Number of weekly backups"), min_value=0, max_value=1000, widget=forms.NumberInput(attrs={"placeholder": "6"}))
    keep_monthly_backups = forms.IntegerField(label=_("Number of monthly backups"), min_value=0, max_value=1000, widget=forms.NumberInput(attrs={"placeholder": "12"}))
    borg_repo_is_on_synology = forms.BooleanField(label=_("Borg Repository is on a Synology NAS"), required=False, widget=forms.CheckboxInput(attrs={"role": "switch"}), help_text = "\n")
    additional_borg_options = forms.CharField(label=_("Additional Borg Options (for experts)"), max_length=1000, required=False, widget=forms.TextInput())


class EmailConfiguration(forms.Form):
    server = forms.CharField(label=_("Email Server"), max_length=100, widget=forms.TextInput(attrs={"placeholder": "mail.example.com"}))
    port = forms.IntegerField(label=_("Email Port"), min_value=0, max_value=10000, widget=forms.NumberInput(attrs={"placeholder": "587"}))
    user = forms.CharField(label=_("Email Username"), max_length=100, widget=forms.TextInput(attrs={"placeholder": "example@example.com"}))
    email = forms.EmailField(label=_("Email Address"), max_length=100, widget=forms.EmailInput(attrs={"placeholder": "example@example.com"}))
    password = forms.CharField(label=_("Email Password"), max_length=100, widget=forms.PasswordInput(attrs={"placeholder": "Password"}),  required=False)
    encryption = forms.ChoiceField(label=_("Email Encryption"), choices=[("TLS", "TLS"), ("SSL", "SSL")], widget=forms.Select(attrs={"class": "form-control"}))
                                                                                                            

class OnlineOfficeInstallationForm(forms.Form):
    # Selection between OnlyOffice and Collabora and nothing
    online_office = forms.ChoiceField(label=_("Online Office"), choices=[("Collabora", _("Collabora")), ("OnlyOffice", _("OnlyOffice")), ("Deactivate", _("Deactivate"))], widget=forms.Select(attrs={"class": "form-control"}))


class AddonForm(forms.Form):
    file = forms.FileField(label=_("Add-on File"))


class ChangeLibreWorkspaceNameForm(forms.Form):
    name = forms.CharField(label=_("New Libre-Workspace Name"), max_length=100, widget=forms.TextInput(), required=False)


class ChangeIpAdressForm(forms.Form):
    ip = forms.GenericIPAddressField(label=_("IP Address"), widget=forms.TextInput(attrs={"placeholder": "0.0.0.0"}))


class MiscellaneousSettingsForm(forms.Form):
    additional_mail_addresses_for_system_mails = forms.CharField(label=_("Additional email addresses for system emails (separate multiple with commas)"), max_length=100, widget=forms.TextInput(), required=False)
    disable_nextcloud_user_administration = forms.BooleanField(label=_("Disable Nextcloud user administration"), required=False, widget=forms.CheckboxInput(attrs={"role": "switch"}), help_text = "\n")
    cpu_warning_threshold = forms.IntegerField(label=_("CPU warning threshold in %"), min_value=0, max_value=100, widget=forms.NumberInput(attrs={"placeholder": "80"}))
    ram_warning_threshold = forms.IntegerField(label=_("RAM warning threshold in %"), min_value=0, max_value=100, widget=forms.NumberInput(attrs={"placeholder": "80"}))
    disk_warning_threshold = forms.IntegerField(label=_("Disk warning threshold in %"), min_value=0, max_value=100, widget=forms.NumberInput(attrs={"placeholder": "90"}))


class AdditionalServicesForm(forms.Form):
    start_additional_services = forms.CharField(label=_("Start command for additional services (Bash code)"), widget=forms.Textarea(), required=False)
    stop_additional_services = forms.CharField(label=_("Stop command for additional services (Bash code)"), widget=forms.Textarea(), required=False)


class AutomaticShutdownForm(forms.Form):
    enabled = forms.BooleanField(label=_("Enable automatic restart/shutdown"), required=False, widget=forms.CheckboxInput(attrs={"role": "switch"}), help_text = "\n")
    type = forms.ChoiceField(label=_("Action"), choices=[("Reboot", _("Reboot")), ("Shutdown", _("Shutdown"))], widget=forms.Select(attrs={"class": "form-control"}))
    time = forms.CharField(label=_("Time (Format: HH:MM)"), max_length=100, widget=forms.TextInput())
    weekday = forms.ChoiceField(label=_("Weekday"), choices=[("daily", _("Daily")), ("0", _("Monday")), ("1", _("Tuesday")), ("2", _("Wednesday")), ("3", _("Thursday")), ("4", _("Friday")), ("5", _("Saturday")), ("6", _("Sunday"))], widget=forms.Select(attrs={"class": "form-control"}))


class DesktopSettingsForm(forms.Form):
    set_desktop_password = forms.CharField(label=_("Set Desktop Password"), max_length=100, widget=forms.PasswordInput(attrs={"placeholder": "Password"}), required=False)


class AdditionalBackupConfigurationForm(forms.Form):
    name = forms.CharField(label=_("Name"), max_length=100)
