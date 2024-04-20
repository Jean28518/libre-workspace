import ldap
import ldap.modlist as modlist
from ldap import LDAPError
from django.conf import settings
import base64
import idm.idm as idm


def is_ldap_fine_and_working():
    """Checks, if we can bind to the server. Also returns None if everythin is okay or ldap is disabled"""
    if not settings.AUTH_LDAP_ENABLED:
        return None
    try:
        conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
        conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)
    except LDAPError as e:
        print("Can't connect to LDAP server: " + str(e))
        return "Login nicht möglich, kontaktiere einen Administrator: Can't connect to LDAP server: " + str(e)
    return None


def get_user_information_of_cn(cn):
    if not settings.AUTH_LDAP_ENABLED:
        if cn.lower() == "administrator":
            return idm.get_admin_user()
        return None

    try:
        conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
        conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)
    except LDAPError as e:
        print("Can't connect to LDAP server: " + str(e))
        return None

    dn = ldap_get_dn_of_cn(cn)

    # Get user with dn
    ldap_reply = conn.search_s(dn, ldap.SCOPE_BASE, "(objectClass=*)", ["cn", "givenName", "sn", "displayName", "mail", "memberOf", "objectGUID", "userAccountControl"])

    
    conn.unbind_s()


    if len(ldap_reply) != 1:
        return None
    
    user_information = {}
    user_information["username"] = ldap_reply[0][1].get("cn", [b""])[0].decode('utf-8')
    user_information["first_name"] = ldap_reply[0][1].get("givenName", [b""])[0].decode('utf-8')
    user_information["last_name"] = ldap_reply[0][1].get("sn", [b""])[0].decode('utf-8')
    user_information["displayName"] = ldap_reply[0][1].get("displayName", [b""])[0].decode('utf-8')
    user_information["mail"] = ldap_reply[0][1].get("mail", [b""])[0].decode('utf-8')
    user_information["objectGUID"] = ldap_reply[0][1].get("objectGUID", [b""])[0].hex()
    user_information["enabled"] = int(ldap_reply[0][1].get("userAccountControl", [b'512'])[0]) & 2 == 0
    user_information["dn"] = dn
    user_information["cn"] = cn

    user_information["groups"] = ldap_reply[0][1].get("memberOf", [])
    for i in range(len(user_information["groups"])):
        user_information["groups"][i] = user_information["groups"][i].decode('utf-8')

    user_information["admin"] = is_user_in_group(user_information, "Administrators")

    return user_information


def is_user_in_group(user_information, group_cn):
    for group in user_information["groups"]:
        if group_cn in group:
            return True
    return False

# Takes user dn and password as string
def is_ldap_user_password_correct(user_dn, password):
    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    try:
        conn.bind_s(user_dn, password)
        conn.unbind_s()
    except ldap.INVALID_CREDENTIALS:
        return False
    return True

def ldap_get_cn_of_dn(dn):
    # If its a cn, return it
    if not "," in dn:
        return dn
    return dn.split(",")[0].split("=")[1]

# Takes user dn and password as string
def set_ldap_user_new_password(user_dn, password):
    cn = ldap_get_cn_of_dn(user_dn)
    if not "," in user_dn:
        user_dn = ldap_get_dn_of_cn(cn)
    if ldap_is_system_user(cn):
        return f"Benutzer '{cn}' ist ein Systembenutzer. Aufgrund technischen Gründen kann das Passwort nicht verändert werden."

    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

    # password has to be set as a UTF-16 string surrounded by a UTF-16 " (yes really!) value on each side.  
    encoded_password = encode_password_for_samba(password)
    try:
        conn.modify_s(user_dn, [(ldap.MOD_REPLACE, 'unicodePwd', [encoded_password])])
    except LDAPError as e:
        return f"Fehler: {str(e)}"
    conn.unbind_s()

def encode_password_for_samba(password_in_plaintext):
    return ('"%s"' % password_in_plaintext).encode('utf-16-le')


# Returns dn of user
def get_user_dn_by_email(email):
    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

    # Search for user
    result = conn.search_s(f"cn=users,{settings.AUTH_LDAP_DC}", ldap.SCOPE_SUBTREE, "mail=" + email)
    conn.unbind_s()
    if len(result) != 1:
        return None
    else:
        return result[0][0]

def ldap_create_user(user_information):

    # Check if username is allowd:
    username = user_information["username"]
    # Only allow lowercase letters, numbers and the following special character: -.
    if username.replace("-", "").replace(".", "").replace("0", "").replace("1", "").replace("2", "").replace("3", "").replace("4", "").replace("5", "").replace("6", "").replace("7", "").replace("8", "").replace("9", "").replace("a", "").replace("b", "").replace("c", "").replace("d", "").replace("e", "").replace("f", "").replace("g", "").replace("h", "").replace("i", "").replace("j", "").replace("k", "").replace("l", "").replace("m", "").replace("n", "").replace("o", "").replace("p", "").replace("q", "").replace("r", "").replace("s", "").replace("t", "").replace("u", "").replace("v", "").replace("w", "").replace("x", "").replace("y", "").replace("z", "").replace("ä", "").replace("ö", "").replace("ü", "") != "":
        return "Der Benutzername darf nur Kleinbuchstaben, Zahlen, Punkt und Bindestrich enthalten"

    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

    # Build modlist
    dn = "cn=" + user_information["username"] + f",cn=users,{settings.AUTH_LDAP_DC}"
    attrs = {}
    attrs['objectclass'] = [b'top', b'person', b'organizationalPerson', b'user']
    attrs['cn'] = [user_information["username"].encode('utf-8')]
    attrs['sAMAccountName'] = [user_information["username"].encode('utf-8')]
    attrs['unicodePwd'] = [encode_password_for_samba(user_information["password"])]
    if user_information.get("first_name", "") != "":
        attrs['givenName'] = [user_information["first_name"].encode('utf-8')]
    if user_information.get("last_name", "") != "":
        attrs['sn'] = [user_information["last_name"].encode('utf-8')]
    if user_information.get("first_name", "") != "" or user_information.get("last_name", "") != "":
        attrs['displayName'] = [f"{user_information.get('first_name', '')} {user_information.get('last_name', '')}".encode('utf-8')]
    if user_information.get("mail", "") != "":
        attrs['mail'] = [user_information["mail"].encode('utf-8')]
    ldif = modlist.addModlist(attrs)

    # Add user
    try:
        conn.add_s(dn, ldif)
    except LDAPError as e:
        return f"Fehler: {str(e)}"
    
    # Add user to all default groups
    groups = ldap_get_all_groups()
    for group in groups:
        if group["defaultGroup"]:
            ldap_add_user_to_group(dn, group["dn"])

    # Enable user
    mod_attrs = [(ldap.MOD_REPLACE, 'userAccountControl', [b'512'])]
    conn.modify_s(dn, mod_attrs)
    
    conn.unbind_s()

    # If user should be admin:
    ldap_ensure_admin_status_of_user(user_information["username"], user_information["admin"])


# Revokes or grants admin rights to a user. If nothing changes, nothing happens.
def ldap_ensure_admin_status_of_user(cn : str, admin : bool):
    dn = ldap_get_dn_of_cn(cn)
    user_information = get_user_information_of_cn(cn)
    if user_information is None:
        return f"Benutzer '{cn}' wurde nicht gefunden."
    current_admin_status = user_information["admin"]
    if admin and not current_admin_status:
        ldap_add_user_to_group(dn, f"cn=Administrators,cn=Builtin,{settings.AUTH_LDAP_DC}")
    elif not admin and current_admin_status:
        ldap_remove_user_from_group(dn, f"cn=Administrators,cn=Builtin,{settings.AUTH_LDAP_DC}")


def ldap_get_all_users():
    if not settings.AUTH_LDAP_ENABLED:
        return []

    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

    # Search for user
    result = conn.search_s(settings.AUTH_LDAP_USER_DN_TEMPLATE.replace('cn=%(user)s,', ""), ldap.SCOPE_SUBTREE, "cn=*")
    conn.unbind_s()
    
    users = []
    for user in result:
        user = user[1]
        if b'person' in user.get("objectClass", []):
            dn = user.get("distinguishedName", [b''])[0].decode('utf-8')
            displayName = user.get("displayName", [b''])[0].decode('utf-8')
            mail = user.get("mail", [b''])[0].decode('utf-8')
            cn = user.get("cn", [b''])[0].decode('utf-8')
            groups = user.get("memberOf", [])
            objectGUID = user.get("objectGUID", [b''])[0].hex()
            enabled = int(user.get("userAccountControl", [b'512'])[0]) & 2 == 0
            for i in range(len(groups)):
                groups[i] = groups[i].decode('utf-8')

            if ldap_is_system_user(cn):
                continue

            users.append({"dn": dn, "displayName": displayName, "mail": mail, "cn": cn, "groups": groups, "objectGUID": objectGUID, "enabled": enabled, "admin": is_user_in_group({"groups": groups}, "Administrators")})
    return users

def ldap_is_system_user(cn):
    hidden_users = settings.HIDDEN_LDAP_USERS.lower()
    hidden_users = hidden_users.split(",")
    cn = cn.lower()
    return cn == "guest" or cn == "krbtgt" or cn == "administrator" or cn == "admin" or cn in hidden_users

def ldap_is_system_group(cn):
    system_groups = ["administrators", "domain admins", "domain computers", "domain guests", "domain users", "enterprise admins", "group policy creator owners", "schema admins", "cert publishers", "dnsadmins", "dnsupdateproxy", "ras and ias servers", "allowed rodc password replication group", "denied rodc password replication group", "read-only domain controllers", "protected users", "enterprise read-only domain controllers", "domain controllers"]
    cn = cn.lower()
    return cn in system_groups

def ldap_update_user(cn, user_information):
    # If ldap not enabled save user settings in the User model
    if not settings.AUTH_LDAP_ENABLED:
        idm.update_user(cn, user_information)
        return


    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

    # Build modlist
    dn = ldap_get_dn_of_cn(cn)
    attrs = {}
    if user_information.get("password", "") != "":
        attrs['unicodePwd'] = [encode_password_for_samba(user_information["password"])]
    attrs['givenName'] = [user_information.get("first_name", "").encode('utf-8')]
    attrs['sn'] = [user_information.get("last_name", "").encode('utf-8')]
    attrs['displayName'] = [user_information.get("displayName", "").encode('utf-8')]
    attrs['mail'] = [user_information.get("mail", "").encode('utf-8')]
    
    for key, value in attrs.items():
        if value == [b""] or value == None:
            attrs[key] = [b" "]
   
    if user_information.get("enabled", "") == True:
        attrs['userAccountControl'] = [b'512']
    else:
        attrs['userAccountControl'] = [b'514']


    old_user_information = get_user_information_of_cn(cn)
    old_attrs = {}
    if old_user_information.get("first_name", "") != "":
        old_attrs['givenName'] = [old_user_information.get("first_name", "").encode('utf-8')]
    if old_user_information.get("last_name", "") != "":
        old_attrs['sn'] = [old_user_information.get("last_name", "").encode('utf-8')]
    if old_user_information.get("displayName", "") != "":
        old_attrs['displayName'] = [old_user_information.get("displayName", "").encode('utf-8')]
    if old_user_information.get("mail", "") != "":
        old_attrs['mail'] = [old_user_information.get("mail", "").encode('utf-8')]
    
    if old_user_information.get("enabled", "") == True:
        old_attrs['userAccountControl'] = [b'512']
    else:
        old_attrs['userAccountControl'] = [b'514']

    ldif = modlist.modifyModlist(old_attrs, attrs)

    if ldif != []:
        # Modify user
        try:
            conn.modify_s(dn, ldif)
        except LDAPError as e:
            return f"Fehler: {str(e)}"

        conn.unbind_s()

    ldap_ensure_admin_status_of_user(cn, user_information["admin"])

# If cn is a dn, return it, else return dn of cn
def ldap_get_dn_of_cn(cn):
    # If its a dn, return it
    if cn.startswith("cn="):
        return cn
    return  settings.AUTH_LDAP_USER_DN_TEMPLATE.replace('%(user)s', cn)

def ldap_delete_user(cn):
    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

    # Build modlist
    dn = ldap_get_dn_of_cn(cn)

    # Delete user
    try:
        conn.delete_s(dn)
    except LDAPError as e:
        return f"Fehler: {str(e)}"

    conn.unbind_s()


def ldap_get_all_groups():
    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

    # Get all Groups: (objectClass=group)
    result = conn.search_s(f"cn=users,{settings.AUTH_LDAP_DC}", ldap.SCOPE_SUBTREE, "(objectClass=group)", ["cn", "description"])
    conn.unbind_s()
   
    groups = []
    for group in result:
        dn = group[0]
        group = group[1]
        cn = group.get("cn", [b''])[0].decode('utf-8')
        description = group.get("description", [b''])[0].decode('utf-8')

        # Check if group is default group
        (description, isDefaultGroup) = ldap_check_if_group_is_default_group(description)

        if ldap_is_system_group(cn):
            continue
        groups.append({"dn": dn, "cn": cn, "description": description, "defaultGroup": isDefaultGroup})
    return groups

# Returns tuple of description (str) and isDefaultGroup (bool)
def ldap_check_if_group_is_default_group(description: str, dontRemoveDefaultGroupOfDescription = False):
    isDefaultGroup = False
    if description.endswith(";defaultGroup"):
        if not dontRemoveDefaultGroupOfDescription:
            description = description[:-13]
        isDefaultGroup = True
    return (description, isDefaultGroup)
    


def apply_default_group_attriubte_to_description(description : str, defaultGroup : bool):
    if defaultGroup:
        if description.endswith(";defaultGroup"):
            return description
        else:
            return description + ";defaultGroup"
    else:
        if description.endswith(";defaultGroup"):
            return description[:-13]
        else:
            return description


def ldap_create_group(group_information):

    # Check if group name is allowd:
    # Only allow lowercase letters, numbers and the following special character: -.
    if group_information["cn"].replace("-", "").replace(".", "").replace("0", "").replace("1", "").replace("2", "").replace("3", "").replace("4", "").replace("5", "").replace("6", "").replace("7", "").replace("8", "").replace("9", "").replace("a", "").replace("b", "").replace("c", "").replace("d", "").replace("e", "").replace("f", "").replace("g", "").replace("h", "").replace("i", "").replace("j", "").replace("k", "").replace("l", "").replace("m", "").replace("n", "").replace("o", "").replace("p", "").replace("q", "").replace("r", "").replace("s", "").replace("t", "").replace("u", "").replace("v", "").replace("w", "").replace("x", "").replace("y", "").replace("z", "").replace("ä", "").replace("ö", "").replace("ü", "") != "":
        return "Der Gruppenname darf nur Kleinbuchstaben, Zahlen, Punkt und Bindestrich enthalten"

    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

    group_information["description"] = apply_default_group_attriubte_to_description(group_information["description"], group_information["defaultGroup"])

    # Build modlist
    dn = "cn=" + group_information["cn"] + f",cn=users,{settings.AUTH_LDAP_DC}"
    attrs = {}
    attrs['objectclass'] = [b'top', b'group']
    attrs['cn'] = [group_information["cn"].encode('utf-8')]
    if group_information.get("description", "") != "":
        attrs['description'] = [group_information["description"].encode('utf-8')]
    ldif = modlist.addModlist(attrs)

    # Add group
    try:
        conn.add_s(dn, ldif)
    except LDAPError as e:
        return f"Fehler: {str(e)}"

    conn.unbind_s()

def ldap_update_group(cn, group_information):
    # We dont want to modify the original dict
    group_information = group_information.copy()

    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

    group_information["description"] = apply_default_group_attriubte_to_description(group_information["description"], group_information["defaultGroup"])

    # Build modlist
    dn = ldap_get_dn_of_cn(cn)
    attrs = {}
    if group_information.get("description", "") != "":
        attrs['description'] = [group_information.get("description", "").encode('utf-8')]

    old_group_information = ldap_get_group_information_of_cn(cn, True)
    old_attrs = {}
    if old_group_information.get("description", "") != "":
        old_attrs['description'] = [old_group_information.get("description", "").encode('utf-8')]

    ldif = modlist.modifyModlist(old_attrs, attrs)
    if ldif != []:
        # Modify group
        try:
            conn.modify_s(dn, ldif)
        except LDAPError as e:
            return f"Fehler: {str(e)}"

    conn.unbind_s()

# Returns an single dict with all information to a group
def ldap_get_group_information_of_cn(cn, dontRemoveDefaultGroupOfDescription = False):
    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

    dn = ldap_get_dn_of_cn(cn)

    # Get group with dn
    ldap_reply = conn.search_s(dn, ldap.SCOPE_BASE, "(objectClass=*)", ["cn", "description"])

    
    conn.unbind_s()


    if len(ldap_reply) != 1:
        return None
    
    group_information = {}
    group_information["dn"] = dn
    group_information["cn"] = ldap_reply[0][1].get("cn", [b""])[0].decode('utf-8')
    group_information["description"] = ldap_reply[0][1].get("description", [b""])[0].decode('utf-8')

    # Check if group is default group
    (group_information["description"], group_information["defaultGroup"]) = ldap_check_if_group_is_default_group(group_information["description"], dontRemoveDefaultGroupOfDescription)

    return group_information

def ldap_delete_group(cn):
    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

    # Build modlist
    dn = ldap_get_dn_of_cn(cn)

    # Delete group
    try:
        conn.delete_s(dn)
    except LDAPError as e:
        return f"Fehler: {str(e)}"

    conn.unbind_s()

def ldap_remove_user_from_group(user_dn, group_dn):
    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)
    mod_attrs = [(ldap.MOD_DELETE, 'member', [user_dn.encode('utf-8')])]
    try:
        conn.modify_s(group_dn, mod_attrs)
    except LDAPError as e:
        return f"Fehler: {str(e)}"
    conn.unbind_s()

def ldap_add_user_to_group(user_dn, group_dn):
    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)
    mod_attrs = [(ldap.MOD_ADD, 'member', [user_dn.encode('utf-8')])]
    try:
        conn.modify_s(group_dn, mod_attrs)
    except LDAPError as e:
        return f"Fehler: {str(e)}"
    conn.unbind_s()


def ldap_disable_user(user_dn):
    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)
    mod_attrs = [(ldap.MOD_REPLACE, 'userAccountControl', [b'514'])]
    try:
        conn.modify_s(user_dn, mod_attrs)
    except LDAPError as e:
        return f"Fehler: {str(e)}"
    conn.unbind_s()


def ldap_enable_user(user_dn):
    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)
    mod_attrs = [(ldap.MOD_REPLACE, 'userAccountControl', [b'512'])]
    try:
        conn.modify_s(user_dn, mod_attrs)
    except LDAPError as e:
        return f"Fehler: {str(e)}"
    conn.unbind_s()
