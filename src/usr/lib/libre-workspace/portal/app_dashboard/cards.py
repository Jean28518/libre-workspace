from .models import DashboardEntry
from django.urls import reverse
import unix.unix_scripts.unix as unix
from oidc_provider.models import Client

def get_card_for_dict(dict : dict):
    return get_card_for(dict["title"], dict["url"], dict["icon_path"], dict["description"])

def get_card_for_dashboard_entry(dashboard_entry):
    icon_path = dashboard_entry.icon_url
    if dashboard_entry.icon:
        icon_path = dashboard_entry.icon.url
    return get_card_for(dashboard_entry.title, dashboard_entry.link, icon_path, dashboard_entry.description)

def get_card_for(title, url, icon_path, description):
    # Add special redirection for sso for element
    if "element." in url and Client.objects.filter(name="Matrix").count() > 0:
        url = f"{url}/#/start_sso"

    return f'''<a class="secondary" href="{url}">
        <article>
            <center>
            <div style="padding: 0.5rem;">
                <img src="{icon_path}" alt="{title}" style="height: 6rem"/>
            </div>
            <p><strong> {title} </strong><br><small>{description}</small></p>
            </center>
        </article>
    </a>'''

def add_all_addon_cards_to_card_data():
    addons = unix.get_all_addon_modules()
    for addon in addons:
        for card in card_data:
            if addon["id"] == card["title"].lower():
                continue
        card_data.append({"order": 10, "title": addon["name"], "url": addon["url"], "icon_path": f"/static/lac/icons/{addon['id']}.{addon.get('icon_file_format', '')}", "description": addon["description"], "keywords": [addon["url"], addon["id"]]})

# Only adds predefined system cards to the database not addon cards
# Also handles if a system card is active or not and updates the link
# Also removes all system cards wich are active but not in the caddyfile
def ensure_all_cards_exist_in_database():
    add_all_addon_cards_to_card_data()
    caddyfile_lines = open("/etc/caddy/Caddyfile", "r").readlines()
    # The cards wich are not in the caddyfile as a list
    remaining_system_cards = list(DashboardEntry.objects.filter(is_system=True).all())
    for card_dat in card_data:
        found_in_caddyfile = False
        if card_dat["title"] == "Verwaltung":
            card_dat["url"] = reverse("dashboard")
            # Set the icon path to the default icon for the management card
            card_dat["icon_path"] = "/static/lac/icons/libre-workspace.webp"
            # Make sure to save the "Verwaltung" card in the database and its changes
            card = DashboardEntry.objects.filter(link=card_dat["url"], is_system=True).first()
            if card:
                # If the card already exists, we update it
                card.title = card_dat["title"]
                card.description = card_dat["description"]
                card.icon_url = card_dat["icon_path"]
                card.order = card_dat["order"]
                card.save()
            found_in_caddyfile = True
        else:
            for line in caddyfile_lines:
                for key in card_dat["keywords"]:
                    if line.startswith(f"{key}."):
                        found_in_caddyfile = True
                        card_dat["url"] = line.split(" ")[0].strip()
                        if not card_dat["url"].startswith("https://"):
                            card_dat["url"] = "https://" + card_dat["url"]
      
        # Only handle the cards wich are in the caddyfile
        if not found_in_caddyfile:
            continue

        # Check if the card is already in the database, if not, add it
        if DashboardEntry.objects.filter(link=card_dat["url"]).count() == 0:
            new_dashboard_entry = DashboardEntry(title=card_dat["title"], description=card_dat["description"], link=card_dat["url"], icon_url=card_dat["icon_path"], is_system=True, order=card_dat["order"])
            new_dashboard_entry.save()
        if card_dat["url"] == "":
            continue
        
        # Sometimes there are multiple cards with the same link, so we need to update all of them
        dashboard_entries = DashboardEntry.objects.filter(link=card_dat["url"])
        for dashboard_entry in dashboard_entries:
            dashboard_entry.is_active = found_in_caddyfile
            dashboard_entry.save()

        # Remove the card from the list of all system cards
        if dashboard_entry in remaining_system_cards:
            remaining_system_cards.remove(dashboard_entry)
   
    # So now we remove all the remaining system cards wich are active but not in the caddyfile
    for system_card in remaining_system_cards:
        DashboardEntry.objects.filter(link=system_card.link).delete()

    
# Keywords are used to find the url in the caddyfile
card_data = [
    {"order": 2,"title": "Nextcloud", "url": "", "icon_path": "/static/lac/icons/nextcloud.webp", "description": "Dateien, Kalender, ...", "keywords": ["cloud", "nextcloud"]},
    {"order": 3,"title": "Cloud Desktop", "url": "", "icon_path": "/static/lac/icons/desktop.webp", "description": "Linux-Desktop im Browser", "keywords": ["desktop", "guacamole"]},
    {"order": 4,"title": "Element", "url": "", "icon_path": "/static/lac/icons/element.webp", "description": "Chat", "keywords": ["element"]},
    {"order": 5,"title": "Jitsi", "url": "", "icon_path": "/static/lac/icons/jitsi.webp", "description": "Videokonferenzen", "keywords": ["jitsi", "meet"]},
    {"order": 6,"title": "Zertifikate", "url": "", "icon_path": "/static/lac/icons/lock.webp", "description": "Für sicheren Zugriff", "keywords": ["certificate", "ssl", "cert"]},
    {"order": 7,"title": "Verwaltung", "url": "/idm/dashboard", "icon_path": "/static/lac/icons/libre-workspace.webp", "description": "Benutzer, Gruppen, ...", "keywords": ["central", "verwaltung", "ldap", "portal"]},
]