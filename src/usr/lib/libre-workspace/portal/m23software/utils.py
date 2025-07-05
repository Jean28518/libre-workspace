import os
import requests


M23_API_KEY = ""
# If file /m23/etc/apiKey exists, read the API key from it
if os.path.exists("/m23/etc/apiKey"):
    with open("/m23/etc/apiKey", "r") as f:
        M23_API_KEY = f.read().strip()
URL_BASE = f"http://localhost:2380/rest.php?api_key={M23_API_KEY}&cmd="

# http://localhost/rest.php?api_key=HY3R8rOC4sadFxvS9ucwAGZNP71oWJV0&cmd=getProfiles
# example: ["Debian 12 KDE"]
def get_profiles():
    """
    Fetches the list of profiles from the m23 API.
    Returns a dictionary with profile names as keys and their IDs as values.
    """
    response = requests.get(f"{URL_BASE}getProfiles")
    if response.status_code == 200:
        profile_names = response.json()
        choices = [(name.replace(" ", ""), name) for name in profile_names]
        return choices
    else:
        raise Exception(f"Failed to fetch profiles: {response.status_code} - {response.text}")




			# /**
			# **description Gives out precalculated network settings (eg. next free IP that can be uses for an m23 client).
			# **url rest.php?api_key=[key]&cmd=getNetworkSettingsProposal
			# **/

			# $proposedNetworkSettings = array();
			# $proposedNetworkSettings['ip'] = CLIENT_getNextFreeIp();
			# $proposedNetworkSettings['netmask'] = getServerNetmask();
			# $proposedNetworkSettings['gateway'] = getServerGateway();

			# $dns1dns2 = getDNSServers();
			# $proposedNetworkSettings['dns1'] = $dns1dns2[0];
			# $proposedNetworkSettings['dns2'] = $dns1dns2[1];

			# $proposedNetworkSettings['bootTypes'] = CClient::getNetworkBootTypesArrayForSelection();
			# echo(json_encode($proposedNetworkSettings));


def is_m23_installed():
    """
    Checks if m23 is installed by verifying the existence of the m23 API key file.
    Returns True if m23 is installed, otherwise False.
    """
    return os.path.exists("/m23/etc/apiKey")


def get_network_settings_proposal():
    """
    Fetches the proposed network settings for a new m23 client.
    Returns a dictionary with the proposed IP, netmask, gateway, DNS servers, and boot types.
    """
    response = requests.get(f"{URL_BASE}getNetworkSettingsProposal")
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch network settings proposal: {response.status_code} - {response.text}")


def install_new_client(client_name, ip, netmask, gateway, dns1, dns2, mac, boottype, login, password, rootpassword, profile):
    """
    Adds a new client to m23 with the specified parameters.
    Returns the response from the m23 API.
    """
    params = {
        "client": client_name,
        "ip": ip,
        "netmask": netmask,
        "gateway": gateway,
        "dns1": dns1,
        "dns2": dns2,
        "mac": mac.lower(),  # Ensure MAC address is lowercase
        "boottype": boottype,
        "login": login,
        "password": password,
        "rootpassword": rootpassword,
        "profile": profile
    }
    
    response = requests.get(f"{URL_BASE}addClient", params=params)
    # print(response.text)

    if "error" in response.text:
        return response.text    
    
    
    if response.status_code == 200:
        return
    else:
        raise Exception(f"Failed to add client: {response.status_code} - {response.text}")
    

def get_client_list(group=None):
    """
    Fetches the list of clients from m23.
    Returns a list of client names.
    """

    group_appendix = ""
    if group:
        group_appendix = f"&group={group}"
    
    response = requests.get(f"{URL_BASE}getClientListDetailed{group_appendix}")
    
    if response.status_code == 200:
        json_dict = response.json()
        clients = []
        # Get all keys from the json dictionary
        for key in json_dict.keys():
            if key == "status" or key == "error_code":
                continue
            client = json_dict[key]
            clients.append(client)
        # print(clients)
        return clients
    else:
        raise Exception(f"Failed to fetch client list: {response.status_code} - {response.text}")
    

def assimilate_client(client, ip, password, ubuntuuser="", clientusesdynamicip=0):
    """
    Assimilates a client into m23.
    Returns the response from the m23 API.
    """
    clientusesdynamicip = 1 if clientusesdynamicip else 0
    params = {
        "client": client,
        "ip": ip,
        "password": password,
        "ubuntuuser": ubuntuuser,
        "clientusesdynamicip": clientusesdynamicip
    }
    
    response = requests.get(f"{URL_BASE}assimilateClient", params=params)
    
    if response.status_code == 200:
        if "error" in response.text:
            return response.text    
        return 
        raise Exception(f"Failed to assimilate client: {response.status_code} - {response.text}")
    
			# /**
			# **description Deletes a client
			# **url rest.php?api_key=[key]&cmd=deleteClient&client=[client]
			# **parameter client: name of the client
			# **/

def delete_client(client):
    """
    Deletes a client from m23.
    Returns the response from the m23 API.
    """
    params = {
        "client": client
    }
    
    response = requests.get(f"{URL_BASE}deleteClient", params=params)
    
    if response.status_code == 200:
        if "error" in response.text:
            return response.text    
        return 
    else:
        raise Exception(f"Failed to delete client: {response.status_code} - {response.text}")
    

def get_groups():
    """
    Fetches the list of groups from m23.
    Returns a list of group names.
    """
    response = requests.get(f"{URL_BASE}getGroupsAndCount")
    # print(response.text)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch groups: {response.status_code} - {response.text}")
    

def create_group(group_name, description=""):
    """
    Adds a new group to m23.
    Returns the response from the m23 API.
    """
    params = {
        "group": group_name,
        "description": description
    }
    
    response = requests.get(f"{URL_BASE}createGroup", params=params)
    
    if response.status_code == 200:
        response = response.json()
        if response.get("error_code", 0) != 0:
            return response.text
        return 
    else:
        raise Exception(f"Failed to add group: {response.status_code} - {response.text}")
    

def detele_group(group_name):
    """
    Deletes a group from m23.
    Returns the response from the m23 API.
    """
    params = {
        "group": group_name
    }
    
    response = requests.get(f"{URL_BASE}deleteGroup", params=params)
    
    if response.status_code == 200:
        if "error" in response.text:
            return response.text    
        return 
    else:
        raise Exception(f"Failed to delete group: {response.status_code} - {response.text}")
    

def add_client_to_group(client_name, group_name):
    """
    Adds a client to a group in m23.
    Returns the response from the m23 API.
    """
    params = {
        "client": client_name,
        "group": group_name
    }
    
    response = requests.get(f"{URL_BASE}addClientToGroup", params=params)
    
    if response.status_code == 200:
        reponse = response.json()
        if reponse.get("error_code", 0) != 0:
            return response.text
        return
        
    else:
        raise Exception(f"Failed to add client to group: {response.status_code} - {response.text}")
    


def add_client_to_groups(client_name, groups):
    """
    Adds a client to multiple groups in m23.
    Returns the response from the m23 API.
    """
    if not isinstance(groups, list):
        raise ValueError("groups must be a list")
    
    if not groups:
        return "No groups selected"
    for group in groups:
        msg = add_client_to_group(client_name, group)
        if msg:
            return msg
        

def reboot_client(client_name):
    """
    Reboots a client in m23.
    Returns the response from the m23 API.
    """
    params = {
        "client": client_name
    }
    
    response = requests.get(f"{URL_BASE}rebootClient", params=params)
    
    if response.status_code == 200:
        response_json = response.json()
        if response_json.get("error_code", 0) != 0:
            return response.text
        return "Client rebooted successfully"
    else:
        raise Exception(f"Failed to reboot client: {response.status_code} - {response.text}")
    

def shutdown_client(client_name):
    """
    Shuts down a client in m23.
    Returns the response from the m23 API.
    """
    params = {
        "client": client_name
    }
    
    response = requests.get(f"{URL_BASE}shutdownClient", params=params)
    
    if response.status_code == 200:
        response_json = response.json()
        if response_json.get("error_code", 0) != 0:
            return response.text
        return "Client shutdown successfully"
    else:
        raise Exception(f"Failed to shutdown client: {response.status_code} - {response.text}")
    

def client_packages(client_name, search, status):
    """
    Fetches the list of packages for a client in m23.
    Returns a list of packages. Does not return packages that are not installed. Use search_client_packages_apt for searching packages e.g..
    """
    params = {
        "client": client_name,
        "search": search,
        "status": status
    }
    
    response = requests.get(f"{URL_BASE}clientPackages", params=params)
    
    if response.status_code == 200:
        packages = response.json()["packages"]
        return packages
    else:
        raise Exception(f"Failed to fetch client packages: {response.status_code} - {response.text}")
    

def search_client_packages_apt(client_name, search):
    """
    Searches for packages in the APT repository for a client in m23.
    Returns a list of packages.
    """
    params = {
        "client": client_name,
        "search": search
    }
    
    response = requests.get(f"{URL_BASE}searchPackages", params=params)
    
    if response.status_code == 200:
        packages = response.json()["packages"]
        return packages
    else:
        raise Exception(f"Failed to search client packages: {response.status_code} - {response.text}")
    

def search_client_packages_flatpak(client_name, search):
    """
    Searches for Flatpak packages for a client in m23.
    Returns a list of Flatpak packages.
    """
    params = {
        "client": client_name,
        "search": search
    }
    
    response = requests.get(f"{URL_BASE}searchFlatpakPackages", params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to search Flatpak packages: {response.status_code} - {response.text}")
    

def install_packages(client_name, packages):
    """
    Installs packages on a client in m23.
    Returns the response from the m23 API.
    """
    if not isinstance(packages, list):
        raise ValueError("packages must be a list")
    
    params = {
        "client": client_name,
        "packages": " ".join(packages)
    }
    
    response = requests.get(f"{URL_BASE}installPackages", params=params)
    
    if response.status_code == 200:
        response_json = response.json()
        if response_json.get("error_code", 0) != 0:
            return response.text
        return "Packages installed successfully"
    else:
        raise Exception(f"Failed to install packages: {response.status_code} - {response.text}")
    

def deinstall_packages(client_name, packages: str):
    """
    Uninstalls packages from a client in m23.
    Returns the response from the m23 API.
    """   
    params = {
        "client": client_name,
        "packages": packages
    }
    
    response = requests.get(f"{URL_BASE}deinstallPackages", params=params)
    
    if response.status_code == 200:
        response_json = response.json()
        if response_json.get("error_code", 0) != 0:
            return response.text
        return "Packages uninstalled successfully"
    else:
        raise Exception(f"Failed to uninstall packages: {response.status_code} - {response.text}")