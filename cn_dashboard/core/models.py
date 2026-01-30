from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserSettings(models.Model):
    user = models.OneToOneField(User, db_index=True, on_delete=models.CASCADE)
    notion_token = models.CharField(max_length=255, blank=True)
    canvas_token = models.CharField(max_length=255, blank=True)
    school_domain = models.CharField(max_length=255, blank=True)
    db_properties = models.JSONField(default=list)
