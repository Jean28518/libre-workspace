from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse
from .utils import get_all_available_addons, install_addon, uninstall_addon
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from unix.unix_scripts import unix
from lac.templates import process_overview_dict, message


@staff_member_required(login_url=settings.LOGIN_URL)
def addon_center(request):
    all_available_addons = get_all_available_addons()
    return render(request, "addon_center/addon_center.html", {
        "addons": all_available_addons,
    })

@staff_member_required(login_url=settings.LOGIN_URL)
def addon_center_install_addon(request, addon_id):
    all_available_addons = get_all_available_addons()
    addon = None
    for addon_s in all_available_addons:
        if addon_s["id"] == addon_id:
            addon = addon_s
            break
    if not addon:
        return message(request, f"Addon {addon_id} not found.", "addon_center")

    msg = install_addon(addon_id)  
    if msg:
        return message(request, msg, "addon_center")


    return message(request, f"Addon {addon_id} is installing. This process takes multiple minutes...", "addon_center")

@staff_member_required(login_url=settings.LOGIN_URL)
def addon_center_uninstall_addon(request, addon_id):
    all_available_addons = get_all_available_addons()
    addon = None
    for addon_s in all_available_addons:
        if addon_s["id"] == addon_id:
            addon = addon_s
            break
    if not addon:
        return message(request, f"Addon {addon_id} not found.", "addon_center")
    
    if not addon["installed"]:
        return message(request, f"Addon {addon_id} is not installed.", "addon_center")

    msg = uninstall_addon(addon_id)
    if msg:
        return message(request, msg, "addon_center")

    return message(request, f"Addon {addon_id} uninstalled successfully.", "addon_center")