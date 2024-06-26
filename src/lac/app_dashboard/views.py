from django.shortcuts import render, redirect
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse

from .models import DashboardEntry
from .forms import DashboardEntryForm
from .cards import *

import idm.idm
import idm.ldap
import idm.views
import unix.unix_scripts.unix as unix

def index(request):
    ensure_all_cards_exist_in_database()
    idm.idm.ensure_superuser_exists()
    if not settings.LINUX_ARBEITSPLATZ_CONFIGURED:
        return redirect("welcome_start")
    
    cards = []
    dashboard_entries = DashboardEntry.objects.all()
    dashboard_entries = sorted(dashboard_entries, key=lambda x: abs(x.order))
    for dashboard_entry in dashboard_entries:
        if not dashboard_entry.is_active:
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

    return render(request, "app_dashboard/index.html", {"request": request, "grid": grid})


@staff_member_required(login_url=settings.LOGIN_URL)
def app_dashboard_entries(request):
    dashboard_entries = DashboardEntry.objects.all()
    dashboard_entries = sorted(dashboard_entries, key=lambda x: x.order)
    dashboard_entries = [dashboard for dashboard in dashboard_entries if not (dashboard.is_system and not dashboard.is_active)]
    return render(request, "app_dashboard/app_dashboard_entries.html", {"request": request, "dashboard_entries": dashboard_entries})

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
    return render(request, "lac/create_x.html", {"request": request, "form": form, "type": "Dasboard-Eintrag", "url": reverse("app_dashboard_entries"), "message": message})


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
        form.fields["link"].disabled = True
        form.fields["is_active"].disabled = True
        delete_url = None
        description = "Hinweis: Dieser Eintrag ist ein Systemeintrag."
    return render(request, "lac/edit_x.html", 
                  {"request": request, 
                   "form": form,
                   "description": description,
                   "name": dashboard_entry.title, 
                   "url": reverse("app_dashboard_entries"), 
                   "message": message, 
                   "delete_url": delete_url})

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
    entries.append({"title": "Libre Workspace Portal", "link": domain, "icon_url": "/static/lac/icons/linux-arbeitsplatz.webp", "description": "Übersicht über alle installierten Apps und Dienste auf dem Portal."})

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