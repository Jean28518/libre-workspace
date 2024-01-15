from django.shortcuts import render, redirect
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.core.files.storage import FileSystemStorage

from .models import DashboardEntry
from .forms import DashboardEntryForm
from .cards import *

import idm.idm
import idm.ldap
import idm.views

# Cache for 10 seconds
@cache_page(10)
def index(request):
    idm.idm.ensure_superuser_exists()
    if not settings.LINUX_ARBEITSPLATZ_CONFIGURED:
        return redirect("welcome_start")
    # Array of strings with html code for cards
    cards = []
    caddyfile_lines = open("/etc/caddy/Caddyfile", "r").readlines()
    for card_dat in card_data:
        if card_dat["title"] == "Verwaltung":
            card_dat["url"] = reverse("dashboard")
            cards.append(get_card_for_dict(card_dat))
            continue
        for line in caddyfile_lines:
           for key in card_dat["keywords"]:
                if line.startswith(f"{key}."):
                    card_dat["url"] = line.split(" ")[0].strip()
                    if not card_dat["url"].startswith("https://"):
                        card_dat["url"] = "https://" + card_dat["url"]
                        cards.append(get_card_for_dict(card_dat))

    # Add cards of the user which are stored in the database
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
        for i in range(3):
            if len(cards) == 0:
                break
            grid[-1].append(cards.pop(0))

    while len(grid[-1]) < 3:
        grid[-1].append("<div></div>")
            
    return render(request, "app_dashboard/index.html", {"request": request, "grid": grid})


@staff_member_required(login_url=settings.LOGIN_URL)
def app_dashboard_entries(request):
    dashboard_entries = DashboardEntry.objects.all()
    dashboard_entries = sorted(dashboard_entries, key=lambda x: x.order)
    return render(request, "app_dashboard/app_dashboard_entries.html", {"request": request, "dashboard_entries": dashboard_entries})

@staff_member_required(login_url=settings.LOGIN_URL)
def new_app_dashboard_entry(request):
    message = ""
    if request.method == "POST":
        print(request.FILES)
        form = DashboardEntryForm(request.POST, request.FILES, auto_id=True)
        if form.is_valid():
            form.save()  
            message = "Das Dashboard wurde erfolgreich erstellt."
        else:
            message = "Es ist ein Fehler aufgetreten: " + str(form.errors)

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
    return render(request, "lac/edit_x.html", 
                  {"request": request, 
                   "form": form, 
                   "name": dashboard_entry.title, 
                   "url": reverse("app_dashboard_entries"), 
                   "message": message, 
                   "delete_url": reverse("delete_app_dashboard_entry", kwargs={"id": id})})

def delete_app_dashboard_entry(request, id):
    object = DashboardEntry.objects.get(id=id)
    object.icon.delete()
    object.delete()

    return redirect("app_dashboard_entries")