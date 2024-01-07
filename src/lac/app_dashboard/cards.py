def get_card_for_dict(dict : dict):
    return get_card_for(dict["title"], dict["url"], dict["icon_path"], dict["description"])

def get_card_for(title, url, icon_path, description):
    return f'''<a class="secondary" href="{url}">
        <article>
            <center>
            <img src="{icon_path}" alt="{title}" style="height: 8rem"/>
            <p><strong> {title} </strong><br><small>{description}</small></p>
            </center>
        </article>
    </a>'''

card_data = [
    {"title": "Nextcloud", "url": "", "icon_path": "/static/lac/icons/nextcloud.webp", "description": "Dateien, Kalender, ...", "keywords": ["cloud", "nextcloud"]},
    {"title": "Rocket.Chat", "url": "", "icon_path": "/static/lac/icons/rocketchat.webp", "description": "Unternehmens-Chat", "keywords": ["chat", "rocketchat"]},
    {"title": "Jitsi", "url": "", "icon_path": "/static/lac/icons/jitsi.webp", "description": "Videokonferenzen", "keywords": ["jitsi", "meet"]},
    {"title": "ERP", "url": "", "icon_path": "/static/lac/icons/erp.webp", "description": "Enterprise Resource Planning", "keywords": ["erp", "erpnext", "kivitendo"]},
    {"title": "NocoDB", "url": "", "icon_path": "/static/lac/icons/nocodb.webp", "description": "Datenbanken", "keywords": ["nocodb", "database", "db"]},
    {"title": "Video", "url": "", "icon_path": "/static/lac/icons/video.webp", "description": "Video-Anleitungen", "keywords": ["video", "youtube", "peertube"]},
    {"title": "Zertifikate", "url": "", "icon_path": "/static/lac/icons/lock.webp", "description": "Für sicheren Zugriff", "keywords": ["certificate", "ssl", "cert"]},
    {"title": "Verwaltung", "url": "/login", "icon_path": "/static/lac/icons/company.webp", "description": "Benutzer, Gruppen, ...", "keywords": ["central", "verwaltung", "ldap"]},
]