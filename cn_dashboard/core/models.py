from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class UserSettings(models.Model):
    user = models.OneToOneField(User, db_index=True, on_delete=models.CASCADE)
    notion_token = models.CharField(max_length=255, blank=True)
    canvas_token = models.CharField(max_length=255, blank=True)
    school_domain = models.CharField(max_length=255, blank=True)
    db_properties = models.JSONField(default=list)
    notion_page_id = models.CharField(max_length=255, blank=True, null=True)
    notion_database_id = models.CharField(max_length=255, blank=True, null=True)
    semester_start_date = models.DateField(blank=True, null=True)
    semester_end_date = models.DateField(blank=True, null=True)
    semester_label = models.CharField(max_length=100, blank=True, null=True)
    semesters_per_year = models.IntegerField(blank=True, null=True)
    years_per_program = models.IntegerField(blank=True, null=True)
    semester_phase_names = models.JSONField(default=list, blank=True)
    semester_phases = models.JSONField(default=list, blank=True)


class SyncHistory(models.Model):
    """Tracks user sync actions: database creation and assignment imports."""
    ACTION_CHOICES = [
        ('create_db', 'Create Database'),
        ('import', 'Import Assignments'),
    ]
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('error', 'Error'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    # For import actions: number of newly created assignments
    created_count = models.IntegerField(default=0)
    # For import actions: number of updated assignments
    updated_count = models.IntegerField(default=0)
    # For import actions: number of errors encountered
    error_count = models.IntegerField(default=0)
    
    # For database creation: the new database ID
    database_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Error messages if any
    error_messages = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_action_display()} ({self.get_status_display()}) - {self.created_at}"
