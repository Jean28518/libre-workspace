from .models import DashboardEntry
from django.urls import reverse
import unix.unix_scripts.unix as unix

def get_card_for_dict(dict : dict):
    return get_card_for(dict["title"], dict["url"], dict["icon_path"], dict["description"])

def get_card_for_dashboard_entry(dashboard_entry):
    icon_path = dashboard_entry.icon_url
    if dashboard_entry.icon:
        icon_path = dashboard_entry.icon.url
    return get_card_for(dashboard_entry.title, dashboard_entry.link, icon_path, dashboard_entry.description)

def get_card_for(title, url, icon_path, description):
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
        card_data.append({"order": 10, "title": addon["name"], "url": addon["url"], "icon_path": f"/static/lac/icons/{addon['id']}.webp", "description": addon["description"], "keywords": [addon["url"], addon["id"]]})

# Only adds predefined system cards to the database not addon cards
def ensure_all_cards_exist_in_database():
    caddyfile_lines = open("/etc/caddy/Caddyfile", "r").readlines()
    for card_dat in card_data:
        found_in_caddyfile = False
        if card_dat["title"] == "Verwaltung":
            card_dat["url"] = reverse("dashboard")
            found_in_caddyfile = True
        else:
            for line in caddyfile_lines:
                for key in card_dat["keywords"]:
                    if line.startswith(f"{key}."):
                        found_in_caddyfile = True
                        card_dat["url"] = line.split(" ")[0].strip()
                        if not card_dat["url"].startswith("https://"):
                            card_dat["url"] = "https://" + card_dat["url"]
        
        # Check if the card is already in the database, if not, add it
        if DashboardEntry.objects.filter(title=card_dat["title"]).count() == 0:
            new_dashboard_entry = DashboardEntry(title=card_dat["title"], description=card_dat["description"], link=card_dat["url"], icon_url=card_dat["icon_path"], is_system=True, order=card_dat["order"])
            new_dashboard_entry.save()
        dashboard_entry = DashboardEntry.objects.get(title=card_dat["title"])
        dashboard_entry.link = card_dat["url"]
        dashboard_entry.is_active = found_in_caddyfile
        dashboard_entry.save()

    
# Keywords are used to find the url in the caddyfile
card_data = [
    {"order": 1,"title": "Rocket.Chat", "url": "", "icon_path": "/static/lac/icons/rocketchat.webp", "description": "Unternehmens-Chat", "keywords": ["chat", "rocketchat"]},
    {"order": 2,"title": "Nextcloud", "url": "", "icon_path": "/static/lac/icons/nextcloud.webp", "description": "Dateien, Kalender, ...", "keywords": ["cloud", "nextcloud"]},
    {"order": 3,"title": "Element", "url": "", "icon_path": "/static/lac/icons/element.webp", "description": "Chat", "keywords": ["element"]},
    {"order": 4,"title": "Jitsi", "url": "", "icon_path": "/static/lac/icons/jitsi.webp", "description": "Videokonferenzen", "keywords": ["jitsi", "meet"]},
    {"order": 5,"title": "ERP", "url": "", "icon_path": "/static/lac/icons/erp.webp", "description": "Enterprise Resource Planning", "keywords": ["erp", "erpnext", "kivitendo"]},
    {"order": 6,"title": "NocoDB", "url": "", "icon_path": "/static/lac/icons/nocodb.webp", "description": "Datenbanken", "keywords": ["nocodb", "database", "db"]},
    {"order": 7,"title": "Video", "url": "", "icon_path": "/static/lac/icons/video.webp", "description": "Video-Anleitungen", "keywords": ["video", "youtube", "peertube"]},
    {"order": 8,"title": "Zertifikate", "url": "", "icon_path": "/static/lac/icons/lock.webp", "description": "Für sicheren Zugriff", "keywords": ["certificate", "ssl", "cert"]},
    {"order": 9,"title": "Verwaltung", "url": "/idm/dashboard", "icon_path": "/static/lac/icons/company.webp", "description": "Benutzer, Gruppen, ...", "keywords": ["central", "verwaltung", "ldap", "portal"]},
]