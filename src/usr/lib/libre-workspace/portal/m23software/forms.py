from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _


def true(value):
    return True

def check_mac_address(value):
    # Simple MAC address validation
    if len(value) != 17 or not all(c in "0123456789ABCDEF:" for c in value.upper()):
        raise forms.ValidationError(_("Invalid MAC address. Please enter a valid MAC address in the format XX:XX:XX:XX:XX:XX."))
    return value

def client_name_validator(value):
    # Check that no space is in the client name and its longer than 1 character
    if " " in value or len(value) < 2:
        raise forms.ValidationError(_("The client name must not contain spaces and must be at least 2 characters long."))
    return value


class M23SoftwareInstallClientForm(forms.Form):

# /**
#           **description Gives out precalculated network settings (eg. next free IP that can be uses for an m23 client).
#           **url rest.php?api_key=[key]&cmd=addClient&client=[client]&ip=[ip]&netmask=[netmask]&gateway=[gateway]&dns1=[dns1]&dns2=[dns2]&mac=[mac]&boottype=[boottype]&login=[login]&password=[password]&rootpassword=[rootpassword]&profile=[profile]
#           **parameter client: client name
#           **parameter ip: IP of the client
#           **parameter netmask: netmask of the client
#           **parameter gateway: gateway of the client
#           **parameter dns1: DNS server 1
#           **parameter dns2: DNS server 2
#           **parameter mac: client MAC
#           **parameter boottype: network boot type
#           **parameter login: name of the user
#           **parameter password: password for the user
#           **parameter rootpassword: root password
#           **parameter profile: Name of the distribution/desktop profile.
#           **/

    client_name = forms.CharField(
        label=_("Client Name"),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _("My Client")}),
        help_text=mark_safe(
            _("Specifies the name of the client. <br>The name must not contain spaces and must be at least 2 characters long.")
        ),
        validators=[client_name_validator]
    )
    client_ip = forms.GenericIPAddressField(
        label=_("Client IP"),
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "1.2.3.4"}),
        help_text=mark_safe(
            _("Specifies the future IP address of the client. <br>The IP address must be within the m23 server's network.")
        ),
    )
    client_netmask = forms.GenericIPAddressField(
        label=_("Netmask"),
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "255.255.255.0"}),
        help_text=mark_safe(
            _("Specifies the netmask of the client. <br>The netmask must be within the m23 server's network.")
        ),
    )
    client_gateway = forms.GenericIPAddressField(
        label=_("Gateway"),
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "1.2.3.1"}),
        help_text=mark_safe(
            _("Specifies the gateway of the client. <br>The gateway must be within the m23 server's network.")
        ),
    )
    client_dns1 = forms.GenericIPAddressField(
        label=_("DNS Server 1"),
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "1.1.1.1"}),
        help_text=mark_safe(
            _("Specifies the first DNS server of the client. <br>The DNS server must be within the m23 server's network.")
        ),
    )
    client_dns2 = forms.GenericIPAddressField(
        label=_("DNS Server 2"),
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "8.8.8.8"}),
        help_text=mark_safe(
            _("Specifies the second DNS server of the client. <br>The DNS server must be within the m23 server's network.")
        ),
    )
    client_mac = forms.CharField(
        label=_("Client MAC"),
        max_length=17,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "00:11:22:33:44:55"}),
        help_text=mark_safe(
            _("Specifies the MAC address of the client. <br>The MAC address must be within the m23 server's network.")
        ),
        validators=[check_mac_address]
    )
    client_boottype = forms.ChoiceField(
        label=_("Boot Type"),
        choices=[

        ],
        required=True,
        help_text=mark_safe(
            _("Specifies the boot type of the client. <br>The boot type must be compatible with the m23 server's network.")
        ),
        validators=[true]
    )
    client_login = forms.CharField(
        label=_("Client Login"),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _("max")}),
    )
    client_password = forms.CharField(
        label=_("Client Password"),
        max_length=100,
        required=True,
        widget=forms.PasswordInput(attrs={"placeholder": ""}),
    )
    client_root_password = forms.CharField(
        label=_("Client Root Password"),
        max_length=100,
        required=True,
        widget=forms.PasswordInput(attrs={"placeholder": ""}),
    )
    profile = forms.ChoiceField(
        label=_("Profile"),
        choices=[
            # ('profile1', 'Profile 1'),
            # ('profile2', 'Profile 2'),
            # Add actual profile choices here
        ],
        required=True,
        help_text=mark_safe(
            _("Specifies the profile of the client. <br>The profile must be available on the m23 server.")
        ),
        validators=[true]

    )