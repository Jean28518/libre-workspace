from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _


def true(value):
    return False

def check_mac_address(value):
    # Simple MAC address validation
    if len(value) != 12 or not all(c in "0123456789ABCDEF" for c in value.upper()):
        raise forms.ValidationError(_("Invalid MAC address. Please enter a valid MAC address in the format XXXXXXXXXXXX."))
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
        widget=forms.TextInput(attrs={"placeholder": _("MyClient")}),
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
        widget=forms.TextInput(attrs={"placeholder": "001122334455"}),
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


class M23SoftwareAddClientForm(forms.Form):
    """
    Form for adding a new client to m23.
    This form is used to collect the necessary information for adding a client.
    """

			# /**
			# **description Adds needed data for assimilating a client.
			# **url rest.php?api_key=[key]&cmd=assimilateClient&client=[client]&ip=[ip]&password=[password]&ubuntuuser=[ubuntuuser]&clientusesdynamicip=[clientusesdynamicip]
			# **parameter client: name of the client
			# **parameter ip: IP of the client
			# **parameter password: root password on Debian systems or combines user/root password on Ubuntu systems
			# **parameter ubuntuuser: name of the Ubuntu user or empty if a Debian system is meant.
			# **parameter clientUsesDynamicIP: if set to 1, the client uses a dynamic IP address
			# **/
    
    client_name = forms.CharField(
        label=_("Client Name"),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _("MyClient")}),
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
            _("Specifies the future IP address of the client. <br>The IP address must be reachable from this server.")
        ),
    )
    client_password = forms.CharField(
        label=_("Administrator password on the client"),
        max_length=100,
        required=True,
        widget=forms.PasswordInput(attrs={"placeholder": ""}),
    )
    client_ubuntu_user = forms.CharField(
        label=_("Ubuntu User"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("ubuntu")}),
        help_text=_("Name of the Ubuntu/Linux Mint/... user. Leave empty if the client is a Debian system.")
    )
    client_uses_dynamic_ip = forms.BooleanField(
        label=_("Client uses dynamic IP"),
        required=False,
        initial=False,
        help_text=_("Check this box if the client uses a dynamic IP address. (DHCP)")
    )


class M23SoftwareAddGroupForm(forms.Form):
    """
    Form for adding a new group to m23.
    This form is used to collect the necessary information for adding a group.
    """

    group_name = forms.CharField(
        label=_("Group Name"),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _("MyGroup")}),
        help_text=_("Specifies the name of the group. The name must not contain spaces and must be at least 2 characters long."),
        validators=[client_name_validator]
    )
    description = forms.CharField(
        label=_("Description"),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("A short description of the group")}),
    )

class M23AddClientToGroupsForm(forms.Form):
    """
    Form for adding a client to groups in m23.
    This form is used to collect the necessary information for adding a client to groups.
    """
    groups = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple,
    )

class M23ClientPackagesFilterForm(forms.Form):
    """
    
    """
    search = forms.CharField(
        label=_("Search"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Search packages...")}),
        help_text=_("Search for packages by name or description.")
    )
    filter_by_action = forms.ChoiceField(
        choices=[
            ("installed", _("Installed")),
            ("removed", _("Removed")),
            ("purged", _("Purged")),
            ("all", _("All")),
        ],
        label=_("Filter by Action"),
        required=False,
        help_text=_("Filter packages by their action status."),
    )


class M23ClientPackageSearchForm(forms.Form):
    """
    Form for searching packages on a client.
    This form is used to collect the necessary information for searching packages.
    """
    search = forms.CharField(
        label=_("Search/Packages to Install"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Search packages...")}),
        help_text=_("Search for packages by name or description or insert all packages to install separated by space")
    )
    package_type = forms.ChoiceField(
        choices=[
            ("apt", _("APT Packages")),
            ("flatpak", _("Flatpak Packages")),
        ],
        label=_("Package Type"),
        required=True,
        help_text=_("Select the type of packages to search for. APT packages are installed via the APT package manager, while Flatpak packages are installed via the Flatpak package manager.")
    )
    install = forms.BooleanField(
        label=_("Install these packages right away"),
        required=False, 
        initial=True,
        help_text=_("Check this box to install the selected packages immediately after searching.")
    )
    
 
class M23ClientRemovePackagesForm(forms.Form):
    """
    Form for removing packages from a client.
    This form is used to collect the necessary information for removing packages.
    """
    packages = forms.CharField(
        label=_("Packages to Remove"),
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={"placeholder": _("package1 package2 package3")}),
        help_text=_("Enter the names of the packages to remove, separated by space.")
    )