from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _


class AddonCreatorForm(forms.Form):
    addon_id = forms.CharField(
        label=_("Addon ID (lowercase and single word)"),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _("nocodb")})
    )
    addon_name = forms.CharField(
        label=_("Addon Name"),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _("Noco DB")})
    )
    addon_description = forms.CharField(
        label=_("Addon Description (max. 10 words)"),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _("Database management")})
    )
    project_homepage = forms.CharField(
        label=_("Project Homepage (optional)"),
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("https://www.nocodb.com")})
    )
    addon_author = forms.CharField(
        label=_("Addon Author"),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _("My Name")})
    )
    addon_author_email = forms.EmailField(
        label=_("Addon Author Email"),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _("mail@example.com")})
    )
    addon_url = forms.CharField(
        label=_("Addon URL (Recommended: similar/same as Addon ID)"),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _("db")})
    )
    addon_docker_compose = forms.CharField(
        label=_("docker-compose.yml Content"),
        widget=forms.Textarea
    )
    addon_internal_port = forms.IntegerField(
        label=_("Internal http-Port for the webserver (>1000)"),
        min_value=1000,
        max_value=65535,
        required=True
    )
    addon_logo = forms.ImageField(
        label=_("Addon Logo (Recommended: 256x256px webp)"),
        required=False
    )