from django import forms
from django.utils.translation import gettext as _

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
            "title": _("Title"),
            "description": _("Description"),
            "link": _("Link"),
            "icon": _("Icon"),
            "order": _("Order (< 0: Before fixed icons, > 0: After fixed icons)"),
            "is_active": _("Active"),
            "groups": _("Groups that can see this entry (comma-separated list). Leave empty to be visible to all. The administrator always sees all entries.")
        }

class DashboardAppearanceForm(forms.Form):
    force_dark_mode = forms.BooleanField(label=_("Force dark mode"), required=False)
    portal_branding_title = forms.CharField(label=_("Portal title"), required=False)
    portal_branding_logo = forms.ImageField(label=_("Portal logo"), required=False, widget=forms.FileInput(attrs={"accept": "image/*"}))
    hide_about = forms.BooleanField(label=_("Hide 'About Libre Workspace' section in footer"), required=False)
    primary_color = forms.CharField(label=_("Primary color (HEX code) (e.g.: #09928b)"), required=False)
    secondary_color = forms.CharField(label=_("Secondary color (HEX code) (e.g.: #07746d)"), required=False)