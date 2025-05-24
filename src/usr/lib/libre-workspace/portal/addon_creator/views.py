from django.shortcuts import render
from django.urls import reverse
from .forms import AddonCreatorForm
from .utils import create_addon
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings

# Create your views here.
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
            
    return render(request, "lac/generic_form.html", {"form": form, "heading": "Add-On Generator", "hide_buttons_top": "True", "action": "Generieren", "url": reverse("addons"), "description": "Hier können Sie in Sekunden ein Addon für Libre-Workspace erstellen. Es wird empfohlen, das Addon nach der Erstellung zu überprüfen und ggf. anzupassen.<br>Weitere Informationen zur Erstellung finden Sie hier: <a href='https://docs.libre-workspace.org/modules/addons.html'>https://docs.libre-workspace.org/modules/addons.html</a>"})
