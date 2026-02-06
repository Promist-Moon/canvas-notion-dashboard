from django.urls import path
from . import views
from integrations import views as integrations_views

app_name = "core"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("configure-secrets/", views.configure_secrets, name="configure_secrets"),
    path("save-db-settings/", views.save_db_settings, name="save_db_settings"),
    path("create-database/", integrations_views.create_database, name="create_database"),
    path("import-assignments/", views.import_assignments, name="import_assignments"),
    path("sync-history/", views.sync_history, name="sync_history"),
]
