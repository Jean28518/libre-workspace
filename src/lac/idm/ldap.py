import ldap
import ldap.modlist as modlist
from ldap import LDAPError
from django.conf import settings
import base64


def get_user_information_of_cn(cn):
    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

    dn = ldap_get_dn_of_cn(cn)

    # Get user with dn
    ldap_reply = conn.search_s(dn, ldap.SCOPE_BASE, "(objectClass=*)", ["cn", "givenName", "sn", "displayName", "mail", "memberOf"])

    
    conn.unbind_s()


    if len(ldap_reply) != 1:
        return None
    
    user_information = {}
    user_information["username"] = ldap_reply[0][1].get("cn", [b""])[0].decode('utf-8')
    user_information["first_name"] = ldap_reply[0][1].get("givenName", [b""])[0].decode('utf-8')
    user_information["last_name"] = ldap_reply[0][1].get("sn", [b""])[0].decode('utf-8')
    user_information["displayName"] = ldap_reply[0][1].get("displayName", [b""])[0].decode('utf-8')
    user_information["mail"] = ldap_reply[0][1].get("mail", [b""])[0].decode('utf-8')

    admin = False
    for group in ldap_reply[0][1].get("memberOf", []):
        if b"Administrators" in group:
            admin = True
            break
    user_information["admin"] = admin

    return user_information



    # if ldap_user is None:
    #     return None
    # print(ldap_user.__dict__)
    # i =  {"username": ldap_user.attrs.get("cn", ""),
    #     "first_name": ldap_user.attrs.get("givenName", ""),
    #     "last_name": ldap_user.attrs.get("sn", ""),
    #     "displayName": ldap_user.attrs.get("displayName", ""),
    #     "mail": ldap_user.attrs.get("mail", ""),
    # }

    # # If some values are empty, set them to "" and return a dict without lists
    # return_value = {}
    # for key, value in i.items():
    #     if type(i[key]) == list:
    #         i[key].append("")
    #         return_value[key] = i[key][0]

    # return_value["groups"] = ldap_user.attrs.get("memberOf", [])
    # admin = False
    # for group in return_value["groups"]:
    #     if "Administrators" in group:
    #         admin = True
    #         break
    # return_value["admin"] = admin
    # return return_value


def update_user_information_ldap(ldap_user, user_information):
    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)
    user_dn = ldap_user.dn

    # Build modlist
    old = {'givenName': ldap_user.attrs.get("givenName", ""),
           'sn': ldap_user.attrs.get("sn", ""),
           'displayName': ldap_user.attrs.get("displayName", ""),
           'mail': ldap_user.attrs.get("mail", ""),
           }
    new = {'givenName': [user_information["first_name"].encode('utf-8')],
            'sn': [user_information["last_name"].encode('utf-8')],
            'displayName': [user_information["displayName"].encode('utf-8')],
            'mail': [user_information["mail"].encode('utf-8')],
           }
    ldif = modlist.modifyModlist(old, new)


    # Modify user
    conn.modify_s(user_dn, ldif)
    conn.unbind_s()


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
    return dn.split(",")[0].split("=")[1]

# Takes user dn and password as string
def set_ldap_user_new_password(user_dn, password):
    cn = ldap_get_cn_of_dn(user_dn)
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
    result = conn.search_s("cn=users,dc=int,dc=de", ldap.SCOPE_SUBTREE, "mail=" + email)
    conn.unbind_s()
    if len(result) != 1:
        return None
    else:
        return result[0][0]

def ldap_create_user(user_information):
    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

    # Build modlist
    dn = "cn=" + user_information["username"] + ",cn=users,dc=int,dc=de"
    attrs = {}
    attrs['objectclass'] = [b'top', b'person', b'organizationalPerson', b'user']
    attrs['cn'] = [user_information["username"].encode('utf-8')]
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

    # Enable user
    mod_attrs = [(ldap.MOD_REPLACE, 'userAccountControl', [b'512'])]
    conn.modify_s(dn, mod_attrs)
    
    conn.unbind_s()

    # # Add user to group
    # conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    # conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)
    # dn = "cn=users,cn=groups,cn=accounts,dc=int,dc=de"
    # mod_attrs = [(ldap.MOD_ADD, 'member', [dn])]
    # conn.modify_s(dn, mod_attrs)
    # conn.unbind_s()

def ldap_get_all_users():
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

            if ldap_is_system_user(cn):
                continue

            users.append({"dn": dn, "displayName": displayName, "mail": mail, "cn": cn})
    return users

def ldap_is_system_user(cn):
    cn = cn.lower()
    return cn == "guest" or cn == "krbtgt" or cn == "administrator" or cn == "admin"

def ldap_update_user(cn, user_information):
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

    ldif = modlist.modifyModlist(old_attrs, attrs)

    # Modify user
    try:
        conn.modify_s(dn, ldif)
    except LDAPError as e:
        return f"Fehler: {str(e)}"

    conn.unbind_s()

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