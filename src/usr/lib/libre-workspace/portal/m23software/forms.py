from django import forms
from django.utils.safestring import mark_safe


def true(value):
    return True

def check_mac_address(value):
    # Simple MAC address validation
    if len(value) != 17 or not all(c in "0123456789ABCDEF:" for c in value.upper()):
        raise forms.ValidationError("Ungültige MAC-Adresse. Bitte geben Sie eine gültige MAC-Adresse im Format XX:XX:XX:XX:XX:XX ein.")
    return value

def client_name_validator(value):
    # Check that no space is in the client name and its longer than 1 character
    if " " in value or len(value) < 2:
        raise forms.ValidationError("Der Clientname darf keine Leerzeichen enthalten und muss mindestens 2 Zeichen lang sein.")
    return value


class M23SoftwareInstallClientForm(forms.Form):

# /**
# 			**description Gives out precalculated network settings (eg. next free IP that can be uses for an m23 client).
# 			**url rest.php?api_key=[key]&cmd=addClient&client=[client]&ip=[ip]&netmask=[netmask]&gateway=[gateway]&dns1=[dns1]&dns2=[dns2]&mac=[mac]&boottype=[boottype]&login=[login]&password=[password]&rootpassword=[rootpassword]&profile=[profile]
# 			**parameter client: client name
# 			**parameter ip: IP of the client
# 			**parameter netmask: netmask of the client
# 			**parameter gateway: gateway of the client
# 			**parameter dns1: DNS server 1
# 			**parameter dns2: DNS server 2
# 			**parameter mac: client MAC
# 			**parameter boottype: network boot type
# 			**parameter login: name of the user
# 			**parameter password: password for the user
# 			**parameter rootpassword: root password
# 			**parameter profile: Name of the distribution/desktop profile.
# 			**/

    client_name = forms.CharField(
        label="Client Name",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Mein Client"}),
        help_text=mark_safe(
            "Gibt den Namen des Clients an. <br>Der Name darf keine Leerzeichen enthalten und muss mindestens 2 Zeichen lang sein."
        ),
        validators=[client_name_validator]
    )
    client_ip = forms.GenericIPAddressField(
        label="Client IP",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "1.2.3.4"}),
        help_text=mark_safe(
            "Gibt die spätere IP-Adresse des Clients an. <br>Die IP-Adresse muss im Netz des m23 Servers liegen."
        ),
    )
    client_netmask = forms.GenericIPAddressField(
        label="Netzmaske",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "255.255.255.0"}),
        help_text=mark_safe(
            "Gibt die Netzmaske des Clients an. <br>Die Netzmaske muss im Netz des m23 Servers liegen."
        ),
    )
    client_gateway = forms.GenericIPAddressField(
        label="Gateway",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "1.2.3.1"}),
        help_text=mark_safe(
            "Gibt das Gateway des Clients an. <br>Das Gateway muss im Netz des m23 Servers liegen."
        ),
    )
    client_dns1 = forms.GenericIPAddressField(
        label="DNS Server 1",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "1.1.1.1"}),
        help_text=mark_safe(
            "Gibt den ersten DNS Server des Clients an. <br>Der DNS Server muss im Netz des m23 Servers liegen."
        ),
    )
    client_dns2 = forms.GenericIPAddressField(
        label="DNS Server 2",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "8.8.8.8"}),
        help_text=mark_safe(
            "Gibt den zweiten DNS Server des Clients an. <br>Der DNS Server muss im Netz des m23 Servers liegen."
        ),
    )
    client_mac = forms.CharField(
        label="Client MAC",
        max_length=17,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "00:11:22:33:44:55"}),
        help_text=mark_safe(
            "Gibt die MAC-Adresse des Clients an. <br>Die MAC-Adresse muss im Netz des m23 Servers liegen."
        ),
        validators=[check_mac_address]
    )
    client_boottype = forms.ChoiceField(
        label="Boottyp",
        choices=[

        ],
        required=True,
        help_text=mark_safe(
            "Gibt den Boottyp des Clients an. <br>Der Boottyp muss im Netz des m23 Servers liegen."
        ),
        validators=[true]
    )
    client_login = forms.CharField(
        label="Client Login",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "max"}),
    )
    client_password = forms.CharField(
        label="Client Passwort",
        max_length=100,
        required=True,
        widget=forms.PasswordInput(attrs={"placeholder": ""}),
    )
    client_root_password = forms.CharField(
        label="Client Root Passwort",
        max_length=100,
        required=True,
        widget=forms.PasswordInput(attrs={"placeholder": ""}),
    )
    profile = forms.ChoiceField(
        label="Profil",
        choices=[
            # ('profile1', 'Profil 1'),
            # ('profile2', 'Profil 2'),
            # Add actual profile choices here
        ],
        required=True,
        help_text=mark_safe(
            "Gibt das Profil des Clients an. <br>Das Profil muss im Netz des m23 Servers liegen."
        ),
        validators=[true]

    )






