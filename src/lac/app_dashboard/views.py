from django.shortcuts import render, redirect
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.urls import reverse

from .cards import *

import idm.idm
import idm.ldap
import idm.views

# Cache for 10 seconds
cache_page(10)
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

