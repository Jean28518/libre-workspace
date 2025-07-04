from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from .forms import M23SoftwareInstallClientForm, M23SoftwareAddClientForm, M23SoftwareAddGroupForm, M23AddClientToGroupsForm
import m23software.utils
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from lac import templates
from django.utils.translation import gettext as _
from lac.templates import message, get_2column_table


@staff_member_required(login_url=settings.LOGIN_URL)
def install_client(request):
    msg = ""
    network_settings_proposal = m23software.utils.get_network_settings_proposal()
    if not network_settings_proposal:
        return render(request, "lac/message.html", {
            "message": _("Failed to fetch network settings proposal. Please check if m23 is installed and configured correctly."),
            "url": reverse("m23software.client_list")
        })
    form = M23SoftwareInstallClientForm()
    if request.method == "POST":
        form = M23SoftwareInstallClientForm(request.POST)
        form.fields["client_boottype"].choices = [
            (boot_type.replace(" ", ""), boot_type) for boot_type in network_settings_proposal.get("bootTypes", [])
        ]
        form.fields["profile"].choices = m23software.utils.get_profiles()
        if form.is_valid():
            cleaned_form = form.cleaned_data
            # Add Client:
            msg = m23software.utils.install_new_client(
                client_name=cleaned_form["client_name"],
                ip=cleaned_form["client_ip"],
                netmask=cleaned_form["client_netmask"],
                gateway=cleaned_form["client_gateway"],
                dns1=cleaned_form["client_dns1"],
                dns2=cleaned_form["client_dns2"],
                mac=cleaned_form["client_mac"],
                boottype=cleaned_form["client_boottype"],
                login=cleaned_form["client_login"],
                password=cleaned_form["client_password"],
                rootpassword=cleaned_form["client_root_password"],
                profile=cleaned_form["profile"]
            )
            if msg:
                return message(request, msg, reverse("m23software.client_list"))
            return message(request, _("Client %(client_name)s has been successfully created.") % {"client_name": cleaned_form["client_name"]}, reverse("m23software.client_list"))
    
    if network_settings_proposal:
        form.fields["client_ip"].initial = network_settings_proposal.get("ip", "")
        form.fields["client_netmask"].initial = network_settings_proposal.get("netmask", "")
        form.fields["client_gateway"].initial = network_settings_proposal.get("gateway", "")
        form.fields["client_dns1"].initial = network_settings_proposal.get("dns1", "")
        form.fields["client_dns2"].initial = network_settings_proposal.get("dns2", "")
        form.fields["client_boottype"].choices = [
            (boot_type.replace(" ", ""), boot_type) for boot_type in network_settings_proposal.get("bootTypes", [])
        ]
    form.fields["profile"].choices = m23software.utils.get_profiles()
    client_username = request.user.username
    form.fields["client_login"].initial = client_username



    return render(request, "lac/create_x.html", {
        "form": form,
        "heading": _("Install Client"),
        "hide_buttons_top": "True",
        "action": _("Install"),
        "url": reverse("m23software.client_list"),
        "description": _("Here you can create an installation client for m23. Please note that the client creation logic still needs to be implemented.")
    })


@staff_member_required(login_url=settings.LOGIN_URL)
def m23_client_list(request):
    """
    View to list all m23 clients.
    """

    # Check if get variable 'group' is set
    filter_by_group = request.GET.get("group", None)
        

    # This function should fetch the list of clients from m23 and render them.
    # For now, we will just return a placeholder response.

    m23_clients = m23software.utils.get_client_list()

    # Filter clients by group if 'group' is specified
    if filter_by_group:
        m23_clients = [client for client in m23_clients if filter_by_group in client.get("groups", [])]

    # for client in m23_clients:
    #     if client["online"]:
    #         client["online"] = _("🟢")
    #     else:
    #         client["online"] = _("🔴")

    add_url = reverse("m23software.add_client")
    install_url = reverse("m23software.install_client")
    group_url = reverse("m23software.group_list")
    groups = m23software.utils.get_groups()
    group_content = ""
    for group in groups:
        if int(group['count']) > 0:
            group['link'] = f"<a href='{reverse('m23software.client_list')}?group={group['groupname']}' class='secondary' style='margin-left: 0.5rem;'>" + f"{_('Filter by %(groupname)s (%(count)s)') % {'groupname': group['groupname'], 'count': group['count']}}</a>"
            group_content += group['link']
    # print("Group content:", group_content)
    overview = templates.process_overview_dict({
        # "elements": [{
        #     "client_name": _("Computer1"),
        #     "ip_address": "1.2.3.4",
        #     "online": _("🟢"),
        # } 
        # ],
        "heading": _("Client List"),
        "elements": m23_clients,
        "t_headings": [_("Client Name"), _("IP Address"), _("Status")],
        "t_keys": ["client", "ip", "statusHR"],
        "element_url_key": "client",
        "element_name": _("Client"),
        "info_url_name": "m23software.client_detail",
        "delete_url_name": "m23software.client_delete",
        "content_above": f"""<a href={add_url} class='primary' role='button' style='margin: 0.5rem;'>{_('Add existing Client')}</a>
                <a href={install_url} class='primary' role='button' style='margin: 0.5rem;'>{_('Install New Client')}</a>
                <a href="{group_url}" class="secondary" role="button" style="margin: 0.5rem;">{_('Manage Groups')}</a>
                <br>{group_content}""",
        "back_url_name": "dashboard",
    })

    return render(request, "lac/overview_x.html", {"overview": overview})


@staff_member_required(login_url=settings.LOGIN_URL)
def m23_client_detail(request, client_name):
    """
    View to show detailed information about a specific m23 client.
    """
    # This function should fetch the detailed information of the client from m23 and render it.
    # For now, we will just return a placeholder response.

    all_clients = m23software.utils.get_client_list()
    client = next((c for c in all_clients if c["client"] == client_name), None)
    if not client:
        return message(request, _("Client %(client_name)s not found.") % {"client_name": client_name}, reverse("m23software.client_list"))
    
    message_content = get_2column_table({
        _("Client Name"): client["client"],
        # _("Status Number"): client["status"],
        _("Status"): client["statusHR"],
        _("IP Address"): client["ip"],
        _("MAC Address"): client["mac"],
        _("Groups"): client["groups"],
        _("Install Date"): client["installDateHR"],
        _("Modify Date"): client["modifyDateHR"],
        _("VM Role"): client["vmRole"] == "1",
        _("VM Software"): client["vmSoftware"] == "1",
        _("All Jobs"): client["jobsAll"],
        _("Waiting Jobs"): client["jobsWaiting"],
        _("All .deb Packages"): client["packagesDebAll"],
    })
    return render(request, "lac/generic_site.html", {
        "heading": _("Client Details"),
        "content": message_content,
        "hide_buttons_top": "True",
        "content_above": f"""
                <a href="{reverse('m23software.add_groups_to_client', args=[client_name])}" class="primary" role="button" style="margin: 0.5rem;">{_('Add Groups to Client')}</a>
                <a href="{reverse('m23software.reboot_client', args=[client_name])}" class="secondary" role="button" style="margin: 0.5rem;">{_('Reboot Client')}</a>
                <a href="{reverse('m23software.shutdown_client', args=[client_name])}" class="secondary" role="button" style="margin: 0.5rem;">{_('Shutdown Client')}</a>
                """,
        "back_url_name": "m23software.client_list",
    })


@staff_member_required(login_url=settings.LOGIN_URL)
def m23_client_delete(request, client_name):
    """
    Delete a client from m23.
    """
    try:
        m23software.utils.delete_client(client_name)
        return message(request, _("Client %(client_name)s has been successfully deleted.") % {"client_name": client_name}, reverse("m23software.client_list"))
    except Exception as e:
        return message(request, str(e), reverse("m23software.client_list"))
    

@staff_member_required(login_url=settings.LOGIN_URL)
def m23_add_client(request):
    """
    Add an existing linux client to m23.
    """
    msg = ""
    form = M23SoftwareAddClientForm()
    if request.method == "POST":
        form = M23SoftwareAddClientForm(request.POST)
        if form.is_valid():
            cleaned_form = form.cleaned_data
            try:
                msg = m23software.utils.assimilate_client(
                    client=cleaned_form["client_name"],
                    ip=cleaned_form["client_ip"],
                    password=cleaned_form["client_password"],
                    ubuntuuser=cleaned_form["client_ubuntu_user"],
                    clientusesdynamicip=cleaned_form["client_uses_dynamic_ip"]
                )
                if msg:
                    return message(request, msg, reverse("m23software.client_list"))
                return message(request, _("Client %(client_name)s has been successfully added.") % {"client_name": cleaned_form["client_name"]}, reverse("m23software.client_list"))
            except Exception as e:
                return message(request, str(e), reverse("m23software.client_list"))
            
    return render(request, "lac/generic_form.html", {
        "form": form,
        "heading": _("Add Client to m23"),
        "hide_buttons_top": "True",
        "action": _("Add"),
        "url": reverse("m23software.client_list"),
        "description": _("Here you can add an existing linux client to the server. Please ensure that the client is reachable and has openssh-server installed.")
    })


def m23_group_list(request):
    """
    View to show an overview of m23 groups.
    """
    # This function should fetch the list of groups from m23 and render them.
    # For now, we will just return a placeholder response.

    groups = m23software.utils.get_groups()
    
    overview = templates.process_overview_dict({
        "elements": groups,
        "t_headings": [_("Group Name"), _("Description"), _("Count")],
        "t_keys": ["groupname", "description", "count"],
        "add_url_name": "m23software.add_group",
        "element_url_key": "groupname",
        "element_name": _("Group"),
        "info_url_name": None,
        "delete_url_name": "m23software.delete_group",
        "back_url_name": "m23software.client_list",
    })

    return render(request, "lac/overview_x.html", {"overview": overview})


@staff_member_required(login_url=settings.LOGIN_URL)
def m23_add_group(request):
    """
    View to add a new group to m23.
    """
    # This function should handle the form submission for adding a new group.
    # For now, we will just return a placeholder response.

    form = M23SoftwareAddGroupForm()
    if request.method == "POST":
        form = M23SoftwareAddGroupForm(request.POST)
        if form.is_valid():
            cleaned_form = form.cleaned_data
            msg = m23software.utils.create_group(cleaned_form["group_name"], cleaned_form["description"])
            if msg:
                return message(request, msg, reverse("m23software.group_list"))
            return message(request, _("Group %(group_name)s has been successfully created.") % {"group_name": cleaned_form["group_name"]}, reverse("m23software.group_list"))
    return render(request, "lac/create_x.html", {
        "form": form,
        "heading": _("Add Group"),
        "hide_buttons_top": "True",
        "action": _("Add"),
        "url": reverse("m23software.group_list"),
        "description": _("Here you can add a new group to m23. Please ensure that the group name is unique and does not already exist.")
    })

@staff_member_required(login_url=settings.LOGIN_URL)
def m23_delete_group(request, group_name):
    """
    View to delete a group from m23.
    """
    # This function should handle the deletion of a group.
    # For now, we will just return a placeholder response.

    try:
        m23software.utils.detele_group(group_name)
        return message(request, _("Group %(groupname)s has been successfully deleted.") % {"groupname": group_name}, reverse("m23software.group_list"))
    except Exception as e:
        return message(request, str(e), reverse("m23software.group_list"))


@staff_member_required(login_url=settings.LOGIN_URL)
def m23_add_groups_to_client(request, client_name):
    """
    View to add groups to a specific client in m23.
    """
    # This function should handle the form submission for adding groups to a client.
    # For now, we will just return a placeholder response.

    all_groups = m23software.utils.get_groups()
    form = M23AddClientToGroupsForm()
    form.fields["groups"].choices = [(group["groupname"], group["groupname"]) for group in all_groups]
    if request.method == "POST":
        form = M23AddClientToGroupsForm(request.POST)
        form.fields["groups"].choices = [(group["groupname"], group["groupname"]) for group in all_groups]
        if form.is_valid():
            cleaned_form = form.cleaned_data
            groups = cleaned_form["groups"]
            # print("Selected groups:", groups)
            if not groups:
                return message(request, _("No groups selected."), reverse("m23software.client_list"))
            msg = m23software.utils.add_client_to_groups(client_name, groups)
            if msg:
                return message(request, msg, reverse("m23software.client_list"))
            return message(request, _("Groups have been successfully added to client %(client_name)s.") % {"client_name": client_name}, reverse("m23software.client_list"))
        
    return render(request, "lac/generic_form.html", {
        "form": form,
        "heading": _("Add Groups to Client"),
        "hide_buttons_top": "True",
        "action": _("Add Groups"),
        "url": reverse("m23software.client_list")
    })


@staff_member_required(login_url=settings.LOGIN_URL)
def m23_shutdown_client(request, client_name):
    """
    View to shutdown a specific client in m23.
    """
    # This function should handle the shutdown of a client.
    # For now, we will just return a placeholder response.

    msg = m23software.utils.shutdown_client(client_name)
    if msg:
        return message(request, msg, reverse("m23software.client_list"))
    
    return message(request, _("Client %(client_name)s has been successfully shut down.") % {"client_name": client_name}, reverse("m23software.client_list"))


@staff_member_required(login_url=settings.LOGIN_URL)
def m23_reboot_client(request, client_name):
    """
    View to reboot a specific client in m23.
    """
    # This function should handle the reboot of a client.
    # For now, we will just return a placeholder response.

    msg = m23software.utils.reboot_client(client_name)
    if msg:
        return message(request, msg, reverse("m23software.client_list"))
    
    return message(request, _("Client %(client_name)s has been successfully rebooted.") % {"client_name": client_name}, reverse("m23software.client_list"))


# @staff_member_required(login_url=settings.LOGIN_URL)
# def m23_package_management(request, client_name):
#     """
#     View to manage packages on a specific client in m23.
#     """
#     # This function should handle the package management for a client.
#     # For now, we will just return a placeholder response.

#     search_term = request.GET.get("search", "")
#     filter_type = request.GET.get("filter", "all")
    
    
#     if filter_type not in ["installed", "removed", "purged", "all"]:
#         return message(request, _("Invalid filter type."), reverse("m23software.client_list"))
    
#     packages = m23software.utils.get_packages(client_name, search_term, filter_type)

#     if not packages:
#         return message(request, _("No packages found for client %(client_name)s.") % {"client_name": client_name}, reverse("m23software.client_list"))
    
#     overview = templates.process_overview_dict({
#         "elements": packages,
#         "t_headings": [_("Package Name"), _("Version"), _("Status")],
#         "t_keys": ["name", "version", "status"],
#         "element_url_key": "name",
#         "element_name": _("Package"),
#         "info_url_name": "m23software.package_detail",
#         "delete_url_name": "m23software.package_remove",
#         "add_url_name": "m23software.package_install",
#         "content_above": f"""
#             <form method="GET" action="{reverse('m23software.package_management', args=[client_name])}">
#                 <input type="text" name="search" value="{search_term}" placeholder="{_('Search packages...')}" />
#                 <select name="filter">
#                     <option value="all" {"selected" if filter_type == "all" else ""}>All</option>
#                     <option value="installed" {"selected" if filter_type == "installed" else ""}>{_('Installed')}</option>
#                     <option value="removed" {"selected" if filter_type == "removed" else ""}>Removed</option>
#                     <option value="purged" {"selected" if filter_type == "purged" else ""}>Purged</option>
#                 </select>
#                 <button type="submit" class="primary">{_('Search')}</button>
#             </form>
#             <a href="{reverse('m23software.package_install', args=[client_name])}" class="primary" role="button" style="margin: 0.5rem;">{_('Install Package')}</a>
#             <a href="{reverse('m23software.package_remove', args=[client_name])}" class="secondary" role="button" style="margin: 0.5rem;">{_('Remove Package')}</a>
#         """,
#         "heading": _("Package Management for %(client_name)s") % {"client_name": client_name},
#         "back_url_name": "m23software.client_detail",
#     })


#     return render(request, "lac/overview_x.html", {"overview": overview})


# @staff_member_required(login_url=settings.LOGIN_URL)
# def m23_package_install(request, client_name):
#     """
#     View to install a package on a specific client in m23.
#     """
#     # This function should handle the installation of a package on a client.
#     # For now, we will just return a placeholder response.

#     if request.method == "POST":
#         package_name = request.POST.get("package_name", "")
#         if not package_name:
#             return message(request, _("Package name is required."), reverse("m23software.package_management", args=[client_name]))
        
#         msg = m23software.utils.install_packages(client_name, [package_name])
#         if msg:
#             return message(request, msg, reverse("m23software.package_management", args=[client_name]))
#         return message(request, _("Package %(package_name)s has been successfully installed on client %(client_name)s.") % {"package_name": package_name, "client_name": client_name}, reverse("m23software.package_management", args=[client_name]))

