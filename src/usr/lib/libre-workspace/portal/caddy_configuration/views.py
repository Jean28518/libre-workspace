from django.shortcuts import render
from django.urls import reverse
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required

from lac.templates import process_overview_dict, message
from .utils import get_all_caddy_entries, delete_caddy_entry, create_reverse_proxy, add_caddy_entry
from .forms import CaddyConfigurationEntryForm, CaddyReverseProxyForm

# Create your views here.
@staff_member_required(login_url=settings.LOGIN_URL)
def caddy_configuration(request):
    all_entries = get_all_caddy_entries()
    manual_add_url = reverse("caddy_configuration_add_entry")
    overview_dict = {
        "title": "Caddy Configuration",
        "add_url_name": "caddy_create_reverse_proxy",
        "elements": all_entries,
        "element_name": "Caddy Entry",
        "t_headings": ["Name", "Endpoint" , "Essential"],
        "t_keys": ["name", "urls_unsafe", "essential"],
        "element_url_key": "id",
        "edit_url_name": "caddy_configuration_edit_entry",
        "delete_url_name": "caddy_configuration_delete_entry",
        "hint": f"Please note that wrong entries can break the Caddy server. Be careful when editing or deleting entries.<br>Here you can add a manual entry: <a href='{manual_add_url}'>Add Manual Entry</a>.",
        "overview_url_name": "caddy_configuration",
        "overview_url_args": [],
        "overview_url_kwargs": {},
    }
    overview = process_overview_dict(overview_dict)
    return render(request, "lac/overview_x.html", {"overview": overview})


@staff_member_required(login_url=settings.LOGIN_URL)
def caddy_configuration_add_entry(request):
    form = CaddyConfigurationEntryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        name = form.cleaned_data["name"]
        block = form.cleaned_data["block"]
        # Here you would typically save the entry to the database or a file
        # For now, we just display a success message
        return message(request, "Caddy entry added successfully!", "caddy_configuration")
    # If the form is not valid or it's a GET request, render the form
    return render(request, "lac/create_x.html", {"form": form, "title": "Add Caddy Entry", "action": "Add", "url": reverse("caddy_configuration")})
    

@staff_member_required(login_url=settings.LOGIN_URL)
def caddy_configuration_edit_entry(request, entry_id):
    all_entries = get_all_caddy_entries()
    # Find the entry to edit by its ID
    entry = next((e for e in all_entries if e.get("id") == entry_id), None)
    if not entry:
        return message(request, "Entry not found.", "caddy_configuration")
    if entry["essential"]:
        return message(request, "This entry is essential and cannot be edited from the web ui.", "caddy_configuration")

    form = CaddyConfigurationEntryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        name = form.cleaned_data["name"]
        block = form.cleaned_data["block"]
        delete_caddy_entry(entry_id)  # Delete
        add_caddy_entry(name, block)  # Add the new entry
        return message(request, "Caddy entry updated successfully!", "caddy_configuration")
    # If the form is not valid or it's a GET request, render the form
    form.fields["name"].initial = entry["name"]
    form.fields["block"].initial = entry["block"]
    return render(request, "lac/edit_x.html", {"form": form, "title": "Edit Caddy Entry", "action": "Edit", "url": reverse("caddy_configuration")})


@staff_member_required(login_url=settings.LOGIN_URL)
def caddy_configuration_delete_entry(request, entry_id):
    all_entries = get_all_caddy_entries()
    # Find the entry to delete by its ID
    entry = next((e for e in all_entries if e.get("id") == entry_id), None)
    if not entry:
        return message(request, "Entry not found.", "caddy_configuration")
    if entry["essential"]:
        return message(request, "This entry is essential and cannot be deleted from the web ui.", "caddy_configuration")
    
    delete_caddy_entry(entry_id)
    return message(request, "Caddy entry deleted successfully!", "caddy_configuration")


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
        msg = create_reverse_proxy(name, domain, port, internal_https, target_url)
        if msg:
            return message(request, msg, "caddy_configuration")
        return message(request, "Reverse proxy entry created successfully!", "caddy_configuration")
    # If the form is not valid or it's a GET request, render the form
    return render(request, "lac/create_x.html", {
        "form": form,
        "title": "Create Reverse Proxy",
        "action": "Create",
        "url": reverse("caddy_configuration"),
    })