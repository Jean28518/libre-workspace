import ldap
import ldap.modlist as modlist
from django.conf import settings
import base64


def get_user_information_of_ldap(ldap_user):
    if ldap_user is None:
        return None
    print(ldap_user.__dict__)
    i =  {"username": ldap_user.attrs.get("cn", ""),
        "first_name": ldap_user.attrs.get("givenName", ""),
        "last_name": ldap_user.attrs.get("sn", ""),
        "displayName": ldap_user.attrs.get("displayName", ""),
        "mail": ldap_user.attrs.get("mail", ""),
    }

    # If some values are empty, set them to "" and return a dict without lists
    return_value = {}
    for key, value in i.items():
        if type(i[key]) == list:
            i[key].append("")
            return_value[key] = i[key][0]

    return_value["groups"] = ldap_user.attrs.get("memberOf", [])
    admin = False
    for group in return_value["groups"]:
        if "Administrators" in group:
            admin = True
            break
    return_value["admin"] = admin
    return return_value


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


# Takes user dn and password as string
def set_ldap_user_new_password(user_dn, password):
    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)

    # password has to be set as a UTF-16 string surrounded by a UTF-16 " (yes really!) value on each side.  
    encoded_password = ('"%s"' % password).encode('utf-16-le')
    conn.modify_s(user_dn, [(ldap.MOD_REPLACE, 'unicodePwd', [encoded_password])])
    conn.unbind_s()


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