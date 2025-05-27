import os
import requests


M23_API_KEY = os.getenv("M23_API_KEY", "")
URL_BASE = f"http://localhost:12934/rest.php?api_key={M23_API_KEY}&cmd="

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


def addClient(client, ip, netmask, gateway, dns1, dns2, mac, boottype, login, password, rootpassword, profile):
    """
    Adds a new client to m23 with the specified parameters.
    Returns the response from the m23 API.
    """
    params = {
        "client": client,
        "ip": ip,
        "netmask": netmask,
        "gateway": gateway,
        "dns1": dns1,
        "dns2": dns2,
        "mac": mac,
        "boottype": boottype,
        "login": login,
        "password": password,
        "rootpassword": rootpassword,
        "profile": profile
    }
    
    response = requests.get(f"{URL_BASE}addClient", params=params)
    
    if response.status_code == 200:
        return response.json()
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
    
    response = requests.get(f"{URL_BASE}getClientList{group_appendix}")
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch client list: {response.status_code} - {response.text}")