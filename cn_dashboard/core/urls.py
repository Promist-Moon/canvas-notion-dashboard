from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("configure-secrets/", views.configure_secrets, name="configure_secrets"),
    path("save-db-settings/", views.save_db_settings, name="save_db_settings"),
]
