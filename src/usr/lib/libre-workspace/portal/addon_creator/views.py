from django.shortcuts import render
from django.urls import reverse
from .forms import AddonCreatorForm
from .utils import create_addon
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.utils.translation import gettext as _

@staff_member_required(login_url=settings.LOGIN_URL)
def addon_creator(request):
    message = ""
    form = AddonCreatorForm()
    if request.method == "POST":
        form = AddonCreatorForm(request.POST, request.FILES)
        if form.is_valid():
            cleaned_form = form.cleaned_data
            # Create the addon
            zip_file_in_bytes = create_addon(cleaned_form)
            # Return the .zip file to the user
            response = HttpResponse(zip_file_in_bytes, content_type="application/zip")
            addon_id = cleaned_form["addon_id"]
            response['Content-Disposition'] = f'attachment; filename="{addon_id}.zip"'
            return response
            
    return render(request, "lac/generic_form.html", {
        "form": form,
        "heading": _("Add-On Generator"),
        "hide_buttons_top": "True",
        "action": _("Generate"),
        "url": reverse("addon_center"),
        "description": _("Here you can create an add-on for Libre-Workspace in seconds. It is recommended to check and, if necessary, adjust the add-on after creation.<br>You can find more information about creating add-ons here: <a href='https://docs.libre-workspace.org/modules/addons.html'>https://docs.libre-workspace.org/modules/addons.html</a>")
    })