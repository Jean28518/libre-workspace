from django import forms
from oidc_provider.models import ResponseType
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _


class BasicUserForm(forms.Form):
    username = forms.CharField(label=_("Username"), max_length=100, disabled=True, required=False)
    first_name = forms.CharField(label=_("First name"), max_length=100, required=False)
    last_name = forms.CharField(label=_("Last name"), max_length=100, required=False)
    displayName = forms.CharField(label=_("Display Name"), max_length=100, required=False)
    mail = forms.EmailField(label=_("Email address"), max_length=100, required=False)


class PasswordForm(forms.Form):
    old_password = forms.CharField(label=_("Old password"), max_length=100, widget=forms.PasswordInput)
    new_password = forms.CharField(label=_("New password"), max_length=100, widget=forms.PasswordInput)
    new_password_repeat = forms.CharField(label=_("Repeat new password"), max_length=100, widget=forms.PasswordInput)


class PasswordResetForm(forms.Form):
    email = forms.EmailField(label=_("Email address"), max_length=100)


class AdministratorUserForm(forms.Form):
    username = forms.CharField(label=_("Username"), max_length=100)
    password = forms.CharField(label=_("Password"), max_length=100, widget=forms.PasswordInput)
    first_name = forms.CharField(label=_("First name"), max_length=100, required=False)
    last_name = forms.CharField(label=_("Last name"), max_length=100, required=False)
    mail = forms.EmailField(label=_("Email address"), max_length=100, required=False)
    admin = forms.BooleanField(label=_("Administrator (If Nextcloud is installed, these changes will take a few minutes there)"), required=False, widget=forms.CheckboxInput)


class AdministratorUserEditForm(forms.Form):
    guid = forms.CharField(label=_("objectGUID"), max_length=100, disabled=True, required=False)
    uidNumber = forms.CharField(label=_("UID Number"), max_length=100, disabled=True, required=False)
    password = forms.CharField(label=_("Set new password"), max_length=100, widget=forms.PasswordInput, required=False)
    first_name = forms.CharField(label=_("First name"), max_length=100, required=False)
    last_name = forms.CharField(label=_("Last name"), max_length=100, required=False)
    displayName = forms.CharField(label=_("Display Name"), max_length=100, required=False)
    mail = forms.EmailField(label=_("Email address"), max_length=100, required=False)
    admin = forms.BooleanField(label=_("Administrator"), required=False, widget=forms.CheckboxInput)
    enabled = forms.BooleanField(label=_("Enabled"), required=False, widget=forms.CheckboxInput)


class GroupCreateForm(forms.Form):
    cn = forms.CharField(label=_("Group name"), max_length=100)
    description = forms.CharField(label=_("Description"), max_length=100, required=False)
    defaultGroup = forms.BooleanField(label=_("Default group (Newly created users will be added to this group from now on)"), required=False, widget=forms.CheckboxInput)
    nextcloud_groupfolder = forms.BooleanField(label=_("Nextcloud group folder"), required=False, widget=forms.CheckboxInput)


class GroupEditForm(forms.Form):
    guid = forms.CharField(label=_("objectGUID"), max_length=100, disabled=True, required=False)
    gidNumber = forms.CharField(label=_("GID Number"), max_length=100, disabled=True, required=False)
    description = forms.CharField(label=_("Description"), max_length=100, required=False)
    defaultGroup = forms.BooleanField(label=_("Default group (Newly created users will be added to this group from now on)"), required=False, widget=forms.CheckboxInput)
    nextcloud_groupfolder = forms.BooleanField(label=_("Nextcloud group folder"), required=False, widget=forms.CheckboxInput)


class OIDCClientForm(forms.Form):
    name = forms.CharField(label=_("Name"), max_length=100)
    client_type = forms.ChoiceField(label=_("Client Type"), choices=[("confidential", _("Confidential")), ("public", _("Public"))])
    response_types = forms.ModelMultipleChoiceField(
        queryset=ResponseType.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )
    redirect_uris = forms.CharField(label=_("Redirect URIs (enter one URI per line)"), widget=forms.Textarea, required=False)
    client_id = forms.CharField(label=_("Client ID"), max_length=100, required=True)
    client_secret = forms.CharField(label=_("Client Secret"), max_length=100, required=True)
    jwt_alg = forms.ChoiceField(label=_("JWT Algorithm"), choices=[("RS256", "RS256"), ("HS256", "HS256")])
    require_consent = forms.BooleanField(label=_("User must consent to data access"), required=False, widget=forms.CheckboxInput)
    reuse_consent = forms.BooleanField(label=_("Reuse consent"), required=False, widget=forms.CheckboxInput)


class TOTPChallengeForm(forms.Form):
    # Select Field for the TOTP device
    totp_device = forms.ChoiceField(label=_("TOTP Device"), choices=[], required=False)
    # Input Field for the TOTP token
    totp_code = forms.CharField(label=_("TOTP Code (Six digits)"), required=True)


class ApiKeyForm(forms.Form):
    name = forms.CharField(label=_("Name"), max_length=100)
    expiration_date = forms.DateField(label=_("Expiration date"), required=False, help_text=_("Optional. If not set, the key never expires."))
    permissions = forms.MultipleChoiceField(
        label=_("Permissions"),
        choices=[
            ("linux_client", _("Linux Client Access")),
            ("administrator", _("Administrator Access")),
        ],
        widget=forms.CheckboxSelectMultiple
    )