from django.db import models


class Site(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    # Simple JSON location placeholder for dev (lon/lat)
    location = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name
