# Import Settings:
import lac.settings as settings
import unix.unix_scripts.unix as unix
import os

# email_settings:
# {
#      "server": "",
#         "port": "",
#         "user": "",
#         "password": "",
#         "encryption": "", # Optios: "TLS", "SSL"
# }
def update_email_settings(email_settings):
    # Change the email settings for lac on the fly
    settings.EMAIL_HOST = email_settings["server"]
    settings.EMAIL_PORT = email_settings["port"]
    settings.EMAIL_HOST_USER = email_settings["user"]
    settings.EMAIL_HOST_EMAIL = email_settings["email"]
    settings.EMAIL_HOST_PASSWORD = email_settings["password"]
    if email_settings["encryption"] == "TLS":
        settings.EMAIL_USE_TLS = "True"
        settings.EMAIL_USE_SSL = "False"
    else:
        settings.EMAIL_USE_TLS = "False"
        settings.EMAIL_USE_SSL = "True"

    # Change email settings in nextcloud if nextcloud is installed
    if unix.is_nextcloud_installed():
        from_adress = email_settings["email"].split("@")[0]
        mail_domain = email_settings["email"].split("@")[1]
        os.system(f'sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ config:system:set mail_smtpauthtype --value="LOGIN"')
        os.system(f'sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ config:system:set mail_smtpmode --value="smtp"')
        os.system(f'sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ config:system:set mail_smtpsecure --value="{email_settings["encryption"]}"')
        os.system(f'sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ config:system:set mail_sendmailmode --value="smtp"')
        os.system(f'sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ config:system:set mail_smtphost --value="{email_settings["server"]}"')
        os.system(f'sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ config:system:set mail_smtpport --value="{email_settings["port"]}"')
        os.system(f'sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ config:system:set mail_domain --value="{mail_domain}"')
        os.system(f'sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ config:system:set mail_from_address --value="{from_adress}"')
        os.system(f'sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ config:system:set mail_smtpauth --value="1"')
        os.system(f'sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ config:system:set mail_smtpname --value="{email_settings["user"]}"')
        os.system(f'sudo -u www-data php {settings.NEXTCLOUD_INSTALLATION_DIRECTORY}/occ config:system:set mail_smtppassword --value="{email_settings["password"]}"')

    
