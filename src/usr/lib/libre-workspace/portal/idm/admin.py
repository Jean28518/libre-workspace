from django.contrib import admin

# Register your models here.
# Register your models here.
from .models import ApiKey, LinuxClientUser

admin.site.register(ApiKey)
admin.site.register(LinuxClientUser)