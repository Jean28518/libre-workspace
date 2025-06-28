from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse
from .utils import get_all_available_addons, install_addon, uninstall_addon
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from unix.unix_scripts import unix
from lac.templates import process_overview_dict, message
from rest_framework import permissions, viewsets
from .serializers import AddonSerializer
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer
from django.utils.translation import gettext as _
from idm.api_permissions import AdministratorPermission



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
        return message(request, _("Addon %(addon_id)s not found.") % {"addon_id": addon_id}, "addon_center")

    msg = install_addon(addon_id)  
    if msg:
        return message(request, msg, "addon_center")


    return message(request, _("Addon %(addon_id)s is installing. This process takes multiple minutes...") % {"addon_id": addon_id}, "addon_center")

@staff_member_required(login_url=settings.LOGIN_URL)
def addon_center_uninstall_addon(request, addon_id):
    all_available_addons = get_all_available_addons()
    addon = None
    for addon_s in all_available_addons:
        if addon_s["id"] == addon_id:
            addon = addon_s
            break
    if not addon:
        return message(request, _("Addon %(addon_id)s not found.") % {"addon_id": addon_id}, "addon_center")
    
    if not addon["installed"]:
        return message(request, _("Addon %(addon_id)s is not installed.") % {"addon_id": addon_id}, "addon_center")

    msg = uninstall_addon(addon_id)
    if msg:
        return message(request, msg, "addon_center")

    return message(request, _("Addon %(addon_id)s uninstalled successfully.") % {"addon_id": addon_id}, "addon_center")


class AddonViewSet(viewsets.ViewSet):
    permission_classes = [AdministratorPermission]

    def list(self, request):
        all_available_addons = get_all_available_addons()
        serializer = AddonSerializer(all_available_addons, many=True)
        return HttpResponse(JSONRenderer().render(serializer.data), content_type="application/json")

    def retrieve(self, request, pk=None):
        all_available_addons = get_all_available_addons()
        addon = next((addon for addon in all_available_addons if addon["id"] == pk), None)
        if not addon:
            return HttpResponse(status=404)
        serializer = AddonSerializer(addon)
        return HttpResponse(JSONRenderer().render(serializer.data), content_type="application/json")
    
    @action(detail=True, methods=['post'], url_name='install')
    def install(self, request, pk=None):
        msg = install_addon(pk)
        if msg:
            return HttpResponse(msg, status=400)
        return HttpResponse(_("Addon %(pk)s is installing. This process takes multiple minutes...") % {"pk": pk}, status=202)
    
    @action(detail=True, methods=['post'], url_name='uninstall')
    def uninstall(self, request, pk=None):
        msg = uninstall_addon(pk)
        if msg:
            return HttpResponse(msg, status=400)
        return HttpResponse(_("Addon %(pk)s uninstalled successfully.") % {"pk": pk}, status=200)