from django.db import models

# Model: dasboard_entry
class DashboardEntry(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=1000, blank=True, default="")
    link = models.CharField(max_length=1000)
    icon = models.FileField(upload_to="dashboard_icons")
    icon_url = models.CharField(max_length=1000, default="")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)
    # comma separated list of group names which can see this entry
    # If this field is empty, all users (also not logged in) can see this entry
    groups = models.CharField(max_length=1000, default="", blank=True) 

    def __str__(self):
        return self.title
    
    def to_dict(self):
        dict = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "link": self.link,
            "icon_url": self.icon_url,
            "order": self.order,
            "is_active": self.is_active,
            "is_system": self.is_system,
            "groups": self.groups
        }
        if self.icon:
            dict["icon_url"] = self.icon.url
        return dict