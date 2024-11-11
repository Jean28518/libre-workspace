from django import forms

from .models import DashboardEntry

class DashboardEntryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DashboardEntryForm, self).__init__(*args, **kwargs)
        self.fields["icon"].required = False
        self.fields["icon"].widget.attrs["accept"] = "image/*"
    class Meta:
        model = DashboardEntry
        fields = ("title", "description", "link", "icon", "order", "is_active", "groups")
        labels = {
            "title": "Titel",
            "description": "Beschreibung",
            "link": "Link",
            "icon": "Icon",
            "order": "Reihenfolge (< 0: Vor den festen Icons, > 0: Hinter den festen Icons)",
            "is_active": "Aktiv",
            "groups": "Gruppen, die diesen Eintrag sehen können (Komma-separierte Liste). Leer lassen, um für alle sichtbar zu sein. Der Administator sieht immer alle Einträge."
        }

class DashboardAppearanceForm(forms.Form):
    force_dark_mode = forms.BooleanField(label="Dunkles Design erzwingen", required=False)
    portal_branding_title = forms.CharField(label="Titel des Portals", required=False)
    portal_branding_logo = forms.ImageField(label="Logo des Portals", required=False, widget=forms.FileInput(attrs={"accept": "image/*"}))
    primary_color = forms.CharField(label="Primärfarbe (HEX-Code) (Bsp: #09928b)", required=False)
    secondary_color = forms.CharField(label="Sekundärfarbe (HEX-Code) (Bsp: #07746d)", required=False)
