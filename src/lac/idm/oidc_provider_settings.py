#from django.utils.translation import ugettext_lazy as _
from oidc_provider.lib.claims import ScopeClaims

from idm.idm import get_user_information
def userinfo(claims, user):
    # Get the get_user_information 
    user_info = get_user_information(str(user))

    # Populate claims dict.
    claims['name'] = user_info['displayName']
    claims['given_name'] = user_info['first_name']
    claims['family_name'] = user_info['last_name']
    claims['middle_name'] = ''
    claims['nickname'] = user_info['username']
    claims['preferred_username'] = user_info['username']
    claims['picture'] = ''
    claims['website'] = ''
    claims['gender'] = ''
    claims['birthdate'] = ''
    claims['zoneinfo'] = ''
    claims['locale'] = ''
    claims['updated_at'] = ''

    claims["profile"] = {
        "name": user_info["displayName"],
        "given_name": user_info["first_name"],
        "family_name": user_info["last_name"],
        "middle_name": "",
        "nickname": user_info["username"],
        "preferred_username": user_info["username"],
        "picture": "",
        "website": "",
        "gender": "",
        "birthdate": "",
        "zoneinfo": "",
        "locale": "",
        "updated_at": "",
    }

    claims['email'] = user_info['mail']
    claims['email_verified'] = True

    claims['address'] = {
        'formatted': '',
        'street_address': '',
        'locality': '',
        'region': '',
        'postal_code': '',
        'country': ''
    }

    return claims


class CustomScopeClaims(ScopeClaims):

    info_guid = (
        (u'GUID'),
        (u'GUID of the user.'),
    )

    def scope_guid(self):
        # self.user - Django user instance.
        # self.userinfo - Dict returned by OIDC_USERINFO function.
        # self.scopes - List of scopes requested.
        # self.client - Client requesting this claims.
        userinfo = get_user_information(str(self.user))
        dic = {
            'guid': str(userinfo['guid']),
            'guid_uppercase': str(userinfo['guid']).upper(),
        }

        return dic
    

    info_groups = (
        (u'Groups'),
        (u'Groups of the user.'),
    )

    def scope_groups(self):
        userinfo = get_user_information(str(self.user))
        group_names = []
        for group in userinfo['groups']:
            # Check if group is a CN then extract the group name (LDAP)
            if str(group).lower().startswith('cn='):
                group_name = str(group)[3:]
                group_name = group_name.split(',')[0]
                group_names.append(group_name)
        dic = {
            'groups': group_names,
            'groups_ldap': userinfo['groups'],
        }

        return dic
