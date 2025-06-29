from django.conf import settings # If you want to access settings variables
import datetime

import app_dashboard.settings
import unix.unix_scripts.unix 

branding = app_dashboard.settings.get_all_values()


def global_settings(request):
    """
    A context processor to add global settings and variables to the template context.
    """
    return {
        'branding': branding,
        'libre_workspace_version': unix.unix_scripts.unix.get_libre_workspace_version(),
    }
