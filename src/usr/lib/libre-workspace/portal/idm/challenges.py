import idm.ldap as ldap
from django.conf import settings
from django.urls import reverse
import unix.email as unix_email
import unix.unix_scripts.unix as unix
import idm.idm
import datetime


def get_all_libre_workspace_challenges(user):
    """Returns an array of dicts with a string and a link to the challenge.
    Only returns challenges which are not already solved."""
    
    challenges = []

    # ADMIN ONLY CHALLENGES

    if user.is_superuser:
        # Challenge 1: Create a new user (if LDAP is enabled)
        if settings.AUTH_LDAP_ENABLED and len(ldap.ldap_get_all_users()) <= 1:
            challenges.append({"text": "Noch bist Du ganz alleine hier. Lasst uns neue Nutzer erstellen!", "link": reverse("create_user")})

        # Challenge 2: Do all variables exist in /etc/libre-workspace/libre-workspace.env?
        if len(unix.get_env_sh_variables().keys()) != 4:
            current_keys = list(unix.get_env_sh_variables().keys())
            challenges.append({"text": f"Es fehlen noch Variablen in der /etc/libre-workspace/libre-workspace.env Datei. Dies muss manuell angepasst werden.<br>Gefundene Variablen: {current_keys}", "link": "https://docs.libre-workspace.org/setup/installation.html#manual-configuration"})

        # Challenge 3: Has the user "administrator" an email?
        if idm.idm.get_admin_user()["mail"].strip() == "":
            challenges.append({"text": "Der Administrator hat noch keine E-Mail Adresse definiert. Diese wird dazu verwendet, um Systemnachrichten zu versenden.", "link": reverse("user_settings")})

        # Challenge 4: Is Backup enabled and configured?
        backup_information = unix.get_borg_information_for_dashboard()
        if backup_information["backup_status"] in ["not_configured", "deactivated"]:
            challenges.append({"text": "Das Backup ist noch nicht konfiguriert oder deaktiviert. Lasst uns dies jetzt einrichten!", "link": reverse("backup_settings")})

        # Challenge 5: Is the status last_backup_failed?
        if backup_information["backup_status"] == "last_backup_failed":
            challenges.append({"text": "Das letzte Backup wurde mit Fehlern beendet.", "link": reverse("unix_index")})
        
        # Challenge 6: Has a backup been performed yet?
        if not backup_information.get("last_backup", False) and not backup_information["backup_status"] == "backup_running":
            challenges.append({"text": "Es wurde noch kein Backup durchgeführt.", "link": reverse("unix_index")})

        # Challenge 7: Is the status last_backup older than 7 days?
        if backup_information.get("last_backup", False):   
            date_string = backup_information["last_backup"]["date"]
            date = datetime.datetime.strptime(date_string, "%Y-%m-%d")
            if (datetime.datetime.now() - date).days > 7:
                challenges.append({"text": "Das letzte vollständige Backup ist älter als 7 Tage.", "link": reverse("unix_index")})

        # Challenge 8: Are the email settings configured and working?
        if not unix_email.are_mail_settings_configured():
            challenges.append({"text": "Die E-Mail Einstellungen sind noch nicht konfiguriert oder funktionieren nicht.", "link": reverse("email_configuration")})


        # Challenge 9: Is libre-workspace-service.service running?
        if not unix.is_unix_service_running():
            challenges.append({"text": "libre-workspace-service.service läuft aktuell nicht. Automatische Aufgaben wie Backups oder Updates werden somit nicht ausgeführt.", "link": reverse("unix_index")})

        # Challenge 10: The system is running longer than 31 days
        system_information = unix.get_system_information()
        if system_information["uptime_in_seconds"] > 31*24*60*60:
            challenges.append({"text": "Der Server läuft schon länger als 31 Tage ohne Neustart. Es ist empfohlen, den Server regelmäßig neu zu starten, um Sicherheitsaktualisierungen anzuwenden.", "link": reverse("unix_index")})

    # USER CHALLENGES (ALSO FOR ADMINS)

    # Challenge: Is 2FA enabled for the current user?
    if not idm.idm.is_2fa_enabled(user):
        challenges.append({"text": "Die Zwei-Faktor-Authentifizierung ist noch nicht aktiviert. Dies erhöht die Sicherheit Deines Kontos.", "link": reverse("otp_settings")})

    return challenges