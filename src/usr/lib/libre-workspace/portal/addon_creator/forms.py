from django import forms
from django.utils.safestring import mark_safe


class AddonCreatorForm(forms.Form):
    addon_id = forms.CharField(
        label="Addon ID (klein und zusammen geschrieben)", 
        max_length=100, 
        required=True, 
        widget=forms.TextInput(attrs={"placeholder": "nocodb"})
    )
    addon_name = forms.CharField(
        label="Addon Name", 
        max_length=100, 
        required=True, 
        widget=forms.TextInput(attrs={"placeholder": "Noco DB"})
    )
    addon_description = forms.CharField(
        label="Addon Beschreibung (max. 10 Wörter)", 
        max_length=100, 
        required=True, 
        widget=forms.TextInput(attrs={"placeholder": "Datenbank-Verwaltung"})
    )
    project_homepage = forms.CharField(
        label="Projekt Webseite (optional)", 
        max_length=200, 
        required=False, 
        widget=forms.TextInput(attrs={"placeholder": "https://www.nocodb.com"})
    )
    addon_author = forms.CharField(
        label="Addon Autor", 
        max_length=100, 
        required=True, 
        widget=forms.TextInput(attrs={"placeholder": "Mein Name"})
    )
    addon_author_email = forms.EmailField(
        label="Addon Autor E-Mail", 
        max_length=100, 
        required=True, 
        widget=forms.TextInput(attrs={"placeholder": "mail@example.com"})
    )
    addon_url = forms.CharField(
        label="Addon URL (Empfohlen: ähnlich/gleich zur Addon ID)", 
        max_length=100, 
        required=True, 
        widget=forms.TextInput(attrs={"placeholder": "db"})
    )
    addon_docker_compose = forms.CharField(
        label="docker-compose.yml Inhalt", 
        widget=forms.Textarea
    )
    addon_internal_port = forms.IntegerField(
        label="Interner http-Port für den Webserver (>1000)", 
        min_value=1000, 
        max_value=65535, 
        required=True
    )
    addon_logo = forms.ImageField(
        label="Addon-Logo (Empfohlen: 256x256px webp)",
        required=False
    )
