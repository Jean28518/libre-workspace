from django.shortcuts import render, redirect
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse

from .models import DashboardEntry
from .forms import DashboardEntryForm, DashboardAppearanceForm
from .cards import *

import idm.idm
import idm.ldap
import idm.views
import unix.unix_scripts.unix as unix

import app_dashboard.settings as app_dashboard_settings

branding = app_dashboard_settings.get_all_values()


def index(request):
    ensure_all_cards_exist_in_database()
    idm.idm.ensure_superuser_exists()
    if not settings.LINUX_ARBEITSPLATZ_CONFIGURED:
        return redirect("welcome_start")
    
    cards = []
    dashboard_entries = DashboardEntry.objects.all()
    dashboard_entries = sorted(dashboard_entries, key=lambda x: abs(x.order))
    user_information = None
    for dashboard_entry in dashboard_entries:
        if not dashboard_entry.is_active:
            continue
        if dashboard_entry.groups and len(dashboard_entry.groups) > 0 and not request.user.is_superuser:
            groups = [group.strip() for group in dashboard_entry.groups.split(",")]
            if not request.user.is_authenticated:
                continue
            if user_information == None:
                user_information = idm.idm.get_user_information(request.user)
            add_card = False
            for group in groups:
                if idm.ldap.is_user_in_group(user_information, group):
                    add_card = True
                    break
            if not add_card:
                continue
        if dashboard_entry.order >= 0:
            cards.append(get_card_for_dashboard_entry(dashboard_entry))
        else:
            cards.insert(0, get_card_for_dashboard_entry(dashboard_entry))

    grid = []
    while len(cards) > 0:
        grid.append([])
        for i in range(4):
            if len(cards) == 0:
                break
            grid[-1].append(cards.pop(0))

    if len(grid) > 0 :
        # If we have 2 cards in the last row, we need to add an empty div to the beginning that the cards are centered
        if len(grid[-1]) == 2:
            grid[-1].insert(0, "<div></div>")
        
        while len(grid[-1]) < 4:
            grid[-1].append("<div></div>")

    return render(request, "app_dashboard/index.html", {"request": request, "grid": grid, "branding": branding})


@staff_member_required(login_url=settings.LOGIN_URL)
def app_dashboard_entries(request):
    dashboard_entries = DashboardEntry.objects.all()
    dashboard_entries = sorted(dashboard_entries, key=lambda x: x.order)
    dashboard_entries = [dashboard for dashboard in dashboard_entries if not (dashboard.is_system and not dashboard.is_active)]
    return render(request, "app_dashboard/app_dashboard_entries.html", {"request": request, "dashboard_entries": dashboard_entries, "branding": branding})

@staff_member_required(login_url=settings.LOGIN_URL)
def new_app_dashboard_entry(request):
    message = ""
    if request.method == "POST":
        print(request.FILES)
        form = DashboardEntryForm(request.POST, request.FILES, auto_id=True)
        if form.is_valid():
            # Check for duplicate title
            if DashboardEntry.objects.filter(title=form.cleaned_data["title"]).count() > 0:
                message = "Es existiert bereits ein Dashboard mit dem Namen."
            else:
                form.save()  
                message = "Das Dashboard wurde erfolgreich erstellt."
        else:
            message = "Es ist ein Fehler aufgetreten: " + str(form.errors)
    else:
        form = DashboardEntryForm()
    return render(request, "lac/create_x.html", {"request": request, "form": form, "type": "Dasboard-Eintrag", "url": reverse("app_dashboard_entries"), "message": message, "branding": branding})


@staff_member_required(login_url=settings.LOGIN_URL)
def edit_app_dashboard_entry(request, id):
    message = ""
    dashboard_entry = DashboardEntry.objects.get(id=id)
    if request.method == "POST":
        form = DashboardEntryForm(request.POST, request.FILES, instance=dashboard_entry, auto_id=True)
        if form.is_valid():
            form.save()
            message = "Das Dashboard wurde erfolgreich bearbeitet."
        else:
            message = "Es ist ein Fehler aufgetreten: " + str(form.errors)

    form = DashboardEntryForm(instance=dashboard_entry)
    description = ""
    delete_url = reverse("delete_app_dashboard_entry", kwargs={"id": id})
    if dashboard_entry.is_system:
        delete_url = None
        description = "Hinweis: Dieser Eintrag ist ein Systemeintrag. Der Link und die Aktivierung werden automatisch aus der Konfiguration generiert."
    return render(request, "lac/edit_x.html", 
                  {"request": request, 
                   "form": form,
                   "description": description,
                   "name": dashboard_entry.title, 
                   "url": reverse("app_dashboard_entries"), 
                   "message": message, 
                   "delete_url": delete_url, 
                   "branding": branding})

def delete_app_dashboard_entry(request, id):
    object = DashboardEntry.objects.get(id=id)
    object.icon.delete()
    object.delete()

    return redirect("app_dashboard_entries")


def entries_json(request):
    """Only returns active ones."""
    entries = DashboardEntry.objects.all()
    entries = sorted(entries, key=lambda x: x.order)
    entries = [entry for entry in entries if entry.is_active]
    entries = [entry.to_dict() for entry in entries]
    # Get the current url over the request object
    current_url = request.build_absolute_uri()
    domain = current_url.split("/")[2]
    # Ensure if under link is only /xxx, it is a relative link we need to add the domain
    for entry in entries:
        if entry["link"].startswith("/"):
            entry["link"] = domain + entry["link"]

    # Add a link to the portal itself
    entries.append({"title": "Libre Workspace Portal", "link": domain, "icon_url": "/static/lac/icons/libre-workspace.webp", "description": "Übersicht über alle installierten Apps und Dienste auf dem Portal."})

    # Add the apps of nextcloud to the specific nextcloud entry if it exists
    # Only choose these apps: "calendar", "contacts", "deck", "notes", "tasks", "collectives"
    nextcloud_entry = None
    for entry in entries:
        if "nextcloud" in entry["title"].lower() or "cloud" in entry["title"].lower():
            nextcloud_entry = entry
            break
    all_installed_nextcloud_apps = unix.get_all_installed_nextcloud_addons()
    nextcloud_apps = []
    for app in all_installed_nextcloud_apps:
        if app in ["calendar", "contacts", "deck", "notes", "tasks", "collectives"]:
            nextcloud_apps.append(app)
    if nextcloud_entry:
        nextcloud_entry["nextcloud_apps"] = nextcloud_apps
    
    return JsonResponse(entries, safe=False)


@staff_member_required(login_url=settings.LOGIN_URL)
def app_dashboard_appearance(request):
    form = DashboardAppearanceForm()
    message = ""
    if request.method == "POST":
        form = DashboardAppearanceForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data["portal_branding_logo"]:
                # Save the logo for static files
                fs = FileSystemStorage(location=settings.MEDIA_ROOT)
                filename = fs.save(form.cleaned_data["portal_branding_logo"].name, form.cleaned_data["portal_branding_logo"])
                app_dashboard_settings.set_value("portal_branding_logo", filename)
            app_dashboard_settings.set_value("force_dark_mode", form.cleaned_data["force_dark_mode"])
            app_dashboard_settings.set_value("portal_branding_title", form.cleaned_data["portal_branding_title"])
            app_dashboard_settings.set_value("primary_color", form.cleaned_data["primary_color"])
            app_dashboard_settings.set_value("secondary_color", form.cleaned_data["secondary_color"])
            message = "Die Einstellungen wurden erfolgreich gespeichert."
    
    form.fields["force_dark_mode"].initial = app_dashboard_settings.get_value("force_dark_mode", False)
    form.fields["portal_branding_title"].initial = app_dashboard_settings.get_value("portal_branding_title", "")
    form.fields["primary_color"].initial = app_dashboard_settings.get_value("primary_color", "")
    form.fields["secondary_color"].initial = app_dashboard_settings.get_value("secondary_color", "")
    if app_dashboard_settings.get_value("portal_branding_logo", "") != "":
        form.fields["portal_branding_logo"].label = "Logo des Portals (Aktuell: " + app_dashboard_settings.get_value("portal_branding_logo", "") + ")"
    reset_url = reverse("reset_app_dashboard_appearance")
    branding = app_dashboard_settings.get_all_values()
    return render(request, "lac/generic_form.html", {"request": request, "form": form, "heading": "Erscheinungsbild", "description": "Diese Einstellungen betreffen alle Benutzer<br>Aktuell wird nur der Bereich des Portals (ohne Verwaltung) angepasst." , "url": "/", "message": message, "action": "Speichern", "hide_buttons_top": True, "additional_content": f"<center><a href='{reset_url}'>Zurücksetzen</a></center>", "branding": branding})


@staff_member_required(login_url=settings.LOGIN_URL)
def reset_app_dashboard_appearance(request):
    app_dashboard_settings.set_value("force_dark_mode", False)
    app_dashboard_settings.set_value("portal_branding_title", "")
    app_dashboard_settings.set_value("portal_branding_logo", "")
    app_dashboard_settings.set_value("portal_branding_favicon", "")
    app_dashboard_settings.set_value("primary_color", "")
    app_dashboard_settings.set_value("secondary_color", "")
    return redirect("app_dashboard_appearance")