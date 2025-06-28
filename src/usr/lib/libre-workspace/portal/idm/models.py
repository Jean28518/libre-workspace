from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.
class ApiKey(models.Model):
    user = models.ForeignKey(
        'auth.User',  
        on_delete=models.CASCADE,
        related_name='api_keys'
    )
    name = models.CharField(
        max_length=128, 
        help_text=_("A descriptive name for the API key")
    )
    key = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    expiration_date = models.DateTimeField(
        null=True, blank=True, help_text=_("The date when the API key will expire")
    )
    permissions = models.TextField(
        help_text=_("Comma-separated list of permissions granted to this API key"), 
        blank=True, 
        default=""
    )
    def __str__(self):
        return self.key

    class Meta:
        verbose_name = _("API Key")
        verbose_name_plural = _("API Keys")
        ordering = ['-created_at']  # Order by creation date, newest first