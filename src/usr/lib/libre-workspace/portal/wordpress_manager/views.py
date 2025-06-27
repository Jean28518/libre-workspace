import time

from django.shortcuts import render
from django.conf import settings
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required

from lac.templates import process_overview_dict, message
from idm.idm import get_user_information
from .utils import get_all_wordpress_sites, delete_wordpress_instance, create_wordpress_instance
from .forms import WordpressInstanceForm

# Create your views here.
# urlpatterns = [
#     path("", views.wordpress_sites, name="wordpress_sites"),
#     path("create_wordpress_instance", views.create_wordpress_instance, name="create_wordpress_instance"),
#     path("edit_wordpress_instance/<int:entry_id>", views.edit_wordpress_instance, name="edit_wordpress_instance"),
#     path("delete_wordpress_instance/<int:entry_id>", views.delete_wordpress_instance, name="delete_wordpress_instance"),
# ]

@staff_member_required(login_url=settings.LOGIN_URL)
def wordpress_sites(request):
    """
    Overview of all WordPress sites.
    """
    overview_dict = {
        "title": "WordPress Sites",
        "elements": get_all_wordpress_sites(),  # This function should return a list of WordPress sites
        "element_name": "WordPress Instance",
        "element_url_key": "id",
        "t_headings": ["Name", "Domain"],
        "t_keys": ["name", "domain"],
        "element_url_key": "id",
        "add_url_name": "create_wordpress_instance",
        # "edit_url_name": "edit_wordpress_instance",
        "delete_url_name": "delete_wordpress_instance",
        "overview_url_name": "wordpress_sites",
    }
    overview = process_overview_dict(overview_dict)
    return render(request, "lac/overview_x.html", {"overview": overview})


@staff_member_required(login_url=settings.LOGIN_URL)
def create_wordpress_instance_view(request):
    """
    Create a new WordPress instance.
    """
    form = WordpressInstanceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        name = form.cleaned_data["name"]
        domain = form.cleaned_data["domain"]
        admin_password = form.cleaned_data["admin_password"]
        admin_email = form.cleaned_data["admin_email"]
        locale = form.cleaned_data["locale"]
        msg = create_wordpress_instance(name, domain, admin_password, admin_email, locale)
        if msg:
            return message(request, msg, "wordpress_sites")
        return message(request, "WordPress instance created successfully!", "wordpress_sites")
    
    # Get the admin user email from the request
    if request.user.is_authenticated:
        form.fields["admin_email"].initial = get_user_information(request.user.username).get("mail", "")
    return render(request, "lac/create_x.html", {"request": request, "form": form, "type": "WordPress Instance", "url": reverse("wordpress_sites")})


@staff_member_required(login_url=settings.LOGIN_URL)
def delete_wordpress_instance_view(request, entry_id):
    """
    Delete a WordPress instance.
    """
    all_sites = get_all_wordpress_sites()
    site = next((s for s in all_sites if s.get("id") == entry_id), None)
    if not site:
        return message(request, "WordPress instance not found.", "wordpress_sites")

    delete_wordpress_instance(entry_id)
    time.sleep(1)
    return message(request, "WordPress instance deleted successfully!", "wordpress_sites")