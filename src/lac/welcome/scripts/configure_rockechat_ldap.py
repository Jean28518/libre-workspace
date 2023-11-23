from pymongo import MongoClient
from datetime import datetime
import os

client = MongoClient('mongodb://mongodb:27017/')

db = client.rocketchat

IP = os.environ['IP']
DOMAIN = os.environ['DOMAIN']
ADMIN_PASSWORD = os.environ['ADMIN_PASSWORD']

SCND_DOMAIN_LABEL = DOMAIN.split(".")[0]
FRST_DOMAIN_LABEL = DOMAIN.split(".")[1]

def update_setting(setting, value):
    db.rocketchat_settings.update_one(
        {"_id": setting},
        {"$set": {
            "value": value,
            # Updated at:
            "_updatedAt": datetime.utcnow()
        }}
        
    )

# Update the setting "LDAP_Host" in the collection rocketchat_settings
update_setting("LDAP_Host", IP)
# Update LDAP_Port
update_setting("LDAP_Port", 636)
# Set LDAP_Authentication to True
update_setting("LDAP_Authentication", True)
# LDAP_Authentication_UserDN is the user that will be used to search for other users in the LDAP server
update_setting("LDAP_Authentication_UserDN", f"cn=Administrator,dc={SCND_DOMAIN_LABEL},dc={FRST_DOMAIN_LABEL}")
# LDAP_Authentication_Password
update_setting("LDAP_Authentication_Password", ADMIN_PASSWORD)
# LDAP_Encryption to ssl
update_setting("LDAP_Encryption", "ssl")
# LDAP_Reject_Unauthorized to False
update_setting("LDAP_Reject_Unauthorized", False)
# LDAP_BaseDN
update_setting("LDAP_BaseDN", f"cn=users,dc={SCND_DOMAIN_LABEL},dc={FRST_DOMAIN_LABEL}")
# LDAP_AD_User_Search_Field to cn,mail
update_setting("LDAP_AD_User_Search_Field", "cn,mail")
# LDAP_Enable to True
update_setting("LDAP_Enable", True)