from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from .forms import M23SoftwareInstallClientForm
import m23software.connector as m23_connector
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from lac import templates



@staff_member_required(login_url=settings.LOGIN_URL)
def install_client(request):
    message = ""
    form = M23SoftwareInstallClientForm()
    if request.method == "POST":
        form = M23SoftwareInstallClientForm(request.POST)
        if form.is_valid():
            cleaned_form = form.cleaned_data
            # Add Client:
            response = m23_connector.add_client(
                client=cleaned_form["client_name"],
                ip=cleaned_form["client_ip"],
                netmask=cleaned_form["client_netmask"],
                gateway=cleaned_form["client_gateway"],
                dns1=cleaned_form["client_dns1"],
                dns2=cleaned_form["client_dns2"],
                mac=cleaned_form["client_mac"],
                boottype=cleaned_form["client_boottype"],
                login=cleaned_form["client_login"],
                password=cleaned_form["client_password"],
                rootpassword=cleaned_form["client_rootpassword"],
                profile=cleaned_form["profile"]
            )
            if response:
                message = "Client erfolgreich erstellt."
            else:
                message = "Fehler beim Erstellen des Clients. Bitte überprüfen Sie die Eingaben."
    
    network_settings_proposal = m23_connector.get_network_settings_proposal()
    if network_settings_proposal:
        form.fields["client_ip"].initial = network_settings_proposal.get("ip", "")
        form.fields["client_netmask"].initial = network_settings_proposal.get("netmask", "")
        form.fields["client_gateway"].initial = network_settings_proposal.get("gateway", "")
        form.fields["client_dns1"].initial = network_settings_proposal.get("dns1", "")
        form.fields["client_dns2"].initial = network_settings_proposal.get("dns2", "")
        form.fields["client_boottype"].choices = [
            (boot_type.replace(" ", ""), boot_type) for boot_type in network_settings_proposal.get("bootTypes", [])
        ]
    form.fields["profile"].choices = m23_connector.get_profiles()
    client_username = request.user.username
    form.fields["client_login"].initial = client_username



    return render(request, "lac/create_x.html", {
        "form": form,
        "heading": "Install Client",
        "hide_buttons_top": "True",
        "action": "Installieren",
        "url": reverse("m23software.client_list"),
        "description": "Hier können Sie einen Installationsclient für m23 erstellen. Bitte beachten Sie, dass die Logik zur Erstellung des Clients noch implementiert werden muss."
    })


def m23_client_list(request):
    """
    View to list all m23 clients.
    """
    # This function should fetch the list of clients from m23 and render them.
    # For now, we will just return a placeholder response.

    m23_clients = m23_connector.get_client_list()
    for client in m23_clients:
        if client["online"]:
            client["online"] = "🟢"
        else:
            client["online"] = "🔴"
    overview = templates.process_overview_dict({
        "elements": [{
            "client_name": "Rechner1",
            "ip_address": "1.2.3.4",
            "online": "🟢",
        } 
        ],
        
        "t_headings": ["Client Name", "IP Address", "Online"],
        "t_keys": ["client_name", "ip_address", "online"],
        "add_url_name": "m23software.install_client",
        "element_url_key": "client_name",
        "element_name": "Client",
        "info_url_name": "m23software.client_detail",
        "delete_url_name": "m23software.client_delete",
    })

    return render(request, "lac/overview_x.html", {"overview": overview})


def m23_client_detail(request, client_name):
    return render(request, "lac/message.html", {
        "message": f"Details for client {client_name} are not yet implemented.",
        "url": "m23software.client_list"
    })


def m23_client_delete(request, client_name):
    return render(request, "lac/message.html", {
        "message": f"Delete functionality for client {client_name} is not yet implemented.",
        "url": "m23software.client_list"
    })