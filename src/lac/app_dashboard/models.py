from django.db import models

# Model: dasboard_entry
class DashboardEntry(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    link = models.CharField(max_length=1000)
    icon = models.FileField(upload_to="dashboard_icons")
    icon_url = models.CharField(max_length=1000, default="")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)

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
            "is_system": self.is_system
        }
        if self.icon:
            dict["icon_url"] = self.icon.url
        return dict