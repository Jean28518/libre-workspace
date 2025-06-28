from django.shortcuts import render
from django.urls import reverse
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import gettext as _

from lac.templates import process_overview_dict, message
from .utils import get_all_caddy_entries, delete_caddy_entry, create_reverse_proxy, add_caddy_entry, create_backup_of_caddyfile
from .forms import CaddyConfigurationEntryForm, CaddyReverseProxyForm

# Create your views here.
@staff_member_required(login_url=settings.LOGIN_URL)
def caddy_configuration(request):
    all_entries = get_all_caddy_entries()
    manual_add_url = reverse("caddy_configuration_add_entry")
    overview_dict = {
        "title": _("Caddy Configuration"),
        "add_url_name": "caddy_create_reverse_proxy",
        "elements": all_entries,
        "element_name": _("Caddy Entry"),
        "t_headings": [_("Name"), _("Endpoint"), _("Essential")],
        "t_keys": ["name", "urls_unsafe", "essential"],
        "element_url_key": "id",
        "edit_url_name": "caddy_configuration_edit_entry",
        "delete_url_name": "caddy_configuration_delete_entry",
        "hint": _("Please note that wrong entries can break the Caddy server. Be careful when editing or deleting entries. If a breakage of Caddy is detected, the old configuration will be tried to be restored after 60 seconds.<br>Here you can add a manual entry: <a href='%(manual_add_url)s'>Add Manual Entry</a>.") % {"manual_add_url": manual_add_url},
        "overview_url_name": "caddy_configuration",
    }
    overview = process_overview_dict(overview_dict)
    return render(request, "lac/overview_x.html", {"overview": overview})


@staff_member_required(login_url=settings.LOGIN_URL)
def caddy_configuration_add_entry(request):
    form = CaddyConfigurationEntryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        name = form.cleaned_data["name"]
        block = form.cleaned_data["block"]
        create_backup_of_caddyfile()  # Create a backup of the Caddyfile before making changes
        add_caddy_entry(name, block)  # Add the new entry
        return message(request, _("Caddy entry added successfully!"), "caddy_configuration")
    # If the form is not valid or it's a GET request, render the form
    return render(request, "lac/create_x.html", {"form": form, "title": _("Add Caddy Entry"), "action": _("Add"), "url": reverse("caddy_configuration")})


@staff_member_required(login_url=settings.LOGIN_URL)
def caddy_configuration_edit_entry(request, entry_id):
    all_entries = get_all_caddy_entries()
    # Find the entry to edit by its ID
    entry = next((e for e in all_entries if e.get("id") == entry_id), None)
    if not entry:
        return message(request, _("Entry not found."), "caddy_configuration")
    if entry["essential"]:
        return message(request, _("This entry is essential and cannot be edited from the web UI."), "caddy_configuration")

    form = CaddyConfigurationEntryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        name = form.cleaned_data["name"]
        block = form.cleaned_data["block"]
        create_backup_of_caddyfile()  # Create a backup of the Caddyfile before making changes
        delete_caddy_entry(entry_id)  # Delete
        add_caddy_entry(name, block)  # Add the new entry
        return message(request, _("Caddy entry updated successfully!"), "caddy_configuration")
    # If the form is not valid or it's a GET request, render the form
    form.fields["name"].initial = entry["name"]
    form.fields["block"].initial = entry["block"]
    return render(request, "lac/edit_x.html", {"form": form, "title": _("Edit Caddy Entry"), "action": _("Edit"), "url": reverse("caddy_configuration")})


@staff_member_required(login_url=settings.LOGIN_URL)
def caddy_configuration_delete_entry(request, entry_id):
    all_entries = get_all_caddy_entries()
    # Find the entry to delete by its ID
    entry = next((e for e in all_entries if e.get("id") == entry_id), None)
    if not entry:
        return message(request, _("Entry not found."), "caddy_configuration")
    if entry["essential"]:
        return message(request, _("This entry is essential and cannot be deleted from the web UI."), "caddy_configuration")

    delete_caddy_entry(entry_id)
    return message(request, _("Caddy entry deleted successfully!"), "caddy_configuration")


@staff_member_required(login_url=settings.LOGIN_URL)
def caddy_create_reverse_proxy(request):
    # This function would handle the creation of a reverse proxy entry
    # For now, we just return a message
    form = CaddyReverseProxyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        name = form.cleaned_data["name"]
        domain = form.cleaned_data["domain"]
        port = form.cleaned_data["port"]
        internal_https = form.cleaned_data["internal_https"]
        target_url = form.cleaned_data["target_url"]
        create_backup_of_caddyfile()  # Create a backup of the Caddyfile before making changes
        msg = create_reverse_proxy(name, domain, port, internal_https, target_url)
        if msg:
            return message(request, msg, "caddy_configuration")
        return message(request, _("Reverse proxy entry created successfully!"), "caddy_configuration")
    # If the form is not valid or it's a GET request, render the form
    return render(request, "lac/create_x.html", {
        "form": form,
        "title": _("Create Reverse Proxy"),
        "action": _("Create"),
        "url": reverse("caddy_configuration"),
    })