# Import Settings:
import lac.settings as settings
import unix.unix_scripts.unix as unix
import os

from ..rocketchat.rocketchat_mongo import update_setting, is_mongodb_available

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
    settings.EMAIL_HOST_PASSWORD = email_settings["password"]
    if email_settings["encryption"] == "TLS":
        settings.EMAIL_USE_TLS = "True"
        settings.EMAIL_USE_SSL = "False"
    else:
        settings.EMAIL_USE_TLS = "False"
        settings.EMAIL_USE_SSL = "True"

    # Change email settings in nextcloud if nextcloud is installed
    if unix.is_nextcloud_available():
        from_adress = email_settings["user"].split("@")[0]
        mail_domain = email_settings["user"].split("@")[1]
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

    
    # Change mail settings in rocket.chat if rocket.chat is installed
    if os.path.isdir("/root/rocket.chat"):
        try:
            update_setting("SMTP_Host", email_settings["server"])
            update_setting("SMTP_Port", email_settings["port"])
            update_setting("SMTP_Username", email_settings["user"])
            update_setting("SMTP_Password", email_settings["password"])
            update_setting("SMTP_Encryption", email_settings["encryption"])
            update_setting("SMTP_From", email_settings["user"])
            update_setting("SMTP_Sendername", "Libre Workspace")
            update_setting("SMTP_Sender_Email", email_settings["user"])
            update_setting("SMTP_Keep_Alive", True)
        except:
            print("Rocket.Chat is not installed.")
            pass
    
