from django import forms

from .models import DashboardEntry

class DashboardEntryForm(forms.ModelForm):
    class Meta:
        model = DashboardEntry
        fields = ("title", "description", "link", "icon", "order", "is_active")
        labels = {
            "title": "Titel",
            "description": "Beschreibung",
            "link": "Link",
            "icon": "Icon",
            "order": "Reihenfolge (< 0: Vor den festen Icons, > 0: Hinter den festen Icons)",
            "is_active": "Aktiv",
        }