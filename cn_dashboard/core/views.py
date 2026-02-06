from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import UserSettings

from integrations.user import User as IntegrationUser

def landing(request):
    if request.user.is_authenticated:
        settings, created = UserSettings.objects.get_or_create(user=request.user)
        return render(request, "core/home.html", {
            'db_properties': settings.db_properties,
            'notion_token': settings.notion_token,
            'canvas_token': settings.canvas_token,
            'school_domain': settings.school_domain,
            'notion_page_id': settings.notion_page_id,
            'notion_database_id': settings.notion_database_id,
        })
    return render(request, "core/welcome.html")

def configure_secrets(request):
    if request.method == "POST":
        n_token = request.POST.get('notion_token')
        c_token = request.POST.get('canvas_token')
        sch = request.POST.get('school_domain')
        n_page = request.POST.get('notion_page_id')
        
        # Save to database
        settings, created = UserSettings.objects.get_or_create(user=request.user)
        settings.notion_token = n_token
        settings.canvas_token = c_token
        settings.school_domain = sch
        settings.notion_page_id = n_page
        settings.save()
        
        return redirect('core:landing')

def save_db_settings(request):
    if request.method == "POST":
        selected_props = request.POST.getlist('properties')
        
        settings = UserSettings.objects.get(user=request.user)
        settings.db_properties = selected_props
        settings.save()
        
        return redirect('core:landing')


@login_required
def import_assignments(request):
    if request.method != 'POST':
        return JsonResponse({"ok": False, "error": "POST required"}, status=400)
    settings, created = UserSettings.objects.get_or_create(user=request.user)
    canvas_token = settings.canvas_token
    notion_token = settings.notion_token
    notion_page_id = settings.notion_page_id
    school_domain = settings.school_domain

    if not canvas_token or not school_domain or not notion_token or not notion_page_id:
        return JsonResponse({"ok": False, "error": "Missing Canvas/Notion credentials or page id"}, status=400)

    # Prefer an explicit notion_database_id (most recently created DB) if available
    db_id = settings.notion_database_id if settings.notion_database_id else None

    integrator = IntegrationUser(
        canvas_token, notion_token, notion_page_id, school_domain, database_id=db_id
    )

    courses = integrator.getAllCourses()
    # This will create DB if needed and upsert new/existing assignments into Notion
    result = integrator.enterAssignmentsToNotionDb(courses)

    created = result.get('created', 0) if isinstance(result, dict) else 0
    updated = result.get('updated', 0) if isinstance(result, dict) else 0
    errors = result.get('errors', []) if isinstance(result, dict) else []

    return JsonResponse({
        "ok": True,
        "created": created,
        "updated": updated,
        "errors": len(errors),
        "error_messages": errors[:10],
    })
