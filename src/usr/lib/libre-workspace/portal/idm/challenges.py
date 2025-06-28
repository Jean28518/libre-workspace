from django.utils.translation import gettext as _
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
            challenges.append({"text": _("You are currently the only user here. Let's create new users!"), "link": reverse("create_user")})

        # Challenge 2: Do all variables exist in /etc/libre-workspace/libre-workspace.env?
        if len(unix.get_env_sh_variables().keys()) != 4:
            current_keys = list(unix.get_env_sh_variables().keys())
            challenges.append({"text": _("Variables are still missing in the /etc/libre-workspace/libre-workspace.env file. This must be adjusted manually.<br>Found variables: %(current_keys)s") % {"current_keys": current_keys}, "link": "https://docs.libre-workspace.org/setup/installation.html#manual-configuration"})

        # Challenge 3: Has the user "administrator" an email?
        if idm.idm.get_admin_user()["mail"].strip() == "":
            challenges.append({"text": _("The administrator has not yet defined an email address. This is used to send system messages."), "link": reverse("user_settings")})

        # Challenge 4: Is Backup enabled and configured?
        backup_information = unix.get_borg_information_for_dashboard()
        if backup_information["backup_status"] in ["not_configured", "deactivated"]:
            challenges.append({"text": _("Backup is not yet configured or is deactivated. Let's set it up now!"), "link": reverse("backup_settings")})

        # Challenge 5: Is the status last_backup_failed?
        if backup_information["backup_status"] == "last_backup_failed":
            challenges.append({"text": _("The last backup finished with errors."), "link": reverse("unix_index")})

        # Challenge 6: Has a backup been performed yet?
        if not backup_information.get("last_backup", False) and not backup_information["backup_status"] == "backup_running":
            challenges.append({"text": _("No backup has been performed yet."), "link": reverse("unix_index")})

        # Challenge 7: Is the status last_backup older than 7 days?
        if backup_information.get("last_backup", False):
            date_string = backup_information["last_backup"]["date"]
            date = datetime.datetime.strptime(date_string, "%Y-%m-%d")
            if (datetime.datetime.now() - date).days > 7:
                challenges.append({"text": _("The last full backup is older than 7 days."), "link": reverse("unix_index")})

        # Challenge 8: Are the email settings configured and working?
        if not unix_email.are_mail_settings_configured():
            challenges.append({"text": _("Email settings are not yet configured or are not working."), "link": reverse("email_configuration")})


        # Challenge 9: Is libre-workspace-service.service running?
        if not unix.is_unix_service_running():
            challenges.append({"text": _("libre-workspace-service.service is not currently running. Automatic tasks like backups or updates will not be executed."), "link": reverse("unix_index")})

        # Challenge 10: The system is running longer than 31 days
        system_information = unix.get_system_information()
        if system_information["uptime_in_seconds"] > 31*24*60*60:
            challenges.append({"text": _("The server has been running for more than 31 days without a restart. It is recommended to restart the server regularly to apply security updates."), "link": reverse("unix_index")})

    # USER CHALLENGES (ALSO FOR ADMINS)

    # Challenge: Is 2FA enabled for the current user?
    if not idm.idm.is_2fa_enabled(user):
        challenges.append({"text": _("Two-factor authentication is not yet enabled. This increases the security of your account."), "link": reverse("otp_settings")})

    return challenges