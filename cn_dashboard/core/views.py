from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash, logout as auth_logout
from .models import UserSettings, SyncHistory

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
        SyncHistory.objects.create(
            user=request.user,
            action='import',
            status='error',
            error_messages=["Missing Canvas/Notion credentials or page id"]
        )
        return JsonResponse({"ok": False, "error": "Missing Canvas/Notion credentials or page id"}, status=400)

    # Prefer an explicit notion_database_id (most recently created DB) if available
    db_id = settings.notion_database_id if settings.notion_database_id else None

    try:
        integrator = IntegrationUser(
            canvas_token,
            notion_token,
            notion_page_id,
            school_domain,
            database_id=db_id,
            db_properties=settings.db_properties,
            semester_start_date=settings.semester_start_date,
            semester_end_date=settings.semester_end_date,
            semester_label=settings.semester_label,
            semester_phases=settings.semester_phases,
        )

        courses = integrator.getAllCourses()
        # This will create DB if needed and upsert new/existing assignments into Notion
        result = integrator.enterAssignmentsToNotionDb(courses)

        created_count = result.get('created', 0) if isinstance(result, dict) else 0
        updated_count = result.get('updated', 0) if isinstance(result, dict) else 0
        errors = result.get('errors', []) if isinstance(result, dict) else []

        # Determine status: error if only errors, success if no errors, error if all failed
        has_successes = created_count > 0 or updated_count > 0
        has_errors = len(errors) > 0
        
        if has_errors and not has_successes:
            status = 'error'
        else:
            status = 'success' if not has_errors else 'error'

        # Log result
        SyncHistory.objects.create(
            user=request.user,
            action='import',
            status=status,
            created_count=created_count,
            updated_count=updated_count,
            error_count=len(errors),
            error_messages=errors[:10]
        )

        return JsonResponse({
            "ok": True,
            "created": created_count,
            "updated": updated_count,
            "errors": len(errors),
            "error_messages": errors[:10],
        })
    except Exception as e:
        SyncHistory.objects.create(
            user=request.user,
            action='import',
            status='error',
            error_count=1,
            error_messages=[str(e)]
        )
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@login_required
def sync_history(request):
    """Display sync history for the current user."""
    records = SyncHistory.objects.filter(user=request.user)[:50]
    return render(request, "core/sync-history.html", {'records': records})

@login_required
def settings(request):
    """Display settings page for the current user."""
    settings, created = UserSettings.objects.get_or_create(user=request.user)
    semester = request.session.get("semester")
    week = request.session.get("week")
    if semester:
        setattr(settings, "semester", semester)
    if week:
        setattr(settings, "week", week)
    return render(request, "core/settings.html", {
        'settings': settings,
    })


@login_required
def change_username(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=400)
    new_username = (request.POST.get("username") or "").strip()
    if new_username:
        request.user.username = new_username
        request.user.save()
    return redirect("core:settings")


@login_required
def save_preferences(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=400)
    semester = request.POST.get("semester")
    week = request.POST.get("week")
    if semester:
        request.session["semester"] = semester
    if week:
        request.session["week"] = week
    return redirect("core:settings")


@login_required
def save_semester_bounds(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=400)

    settings, created = UserSettings.objects.get_or_create(user=request.user)
    start_date_raw = request.POST.get("semester_start_date") or None
    end_date_raw = request.POST.get("semester_end_date") or None
    label = (request.POST.get("semester_label") or "").strip() or None
    semesters_per_year_raw = request.POST.get("semesters_per_year") or None
    years_per_program_raw = request.POST.get("years_per_program") or None
    phase_names_raw = request.POST.get("semester_phase_names") or ""
    phase_names = request.POST.getlist("phase_name")
    phase_starts = request.POST.getlist("phase_start")
    phase_ends = request.POST.getlist("phase_end")
    start_date = None
    end_date = None

    phases = []
    if phase_names or phase_starts or phase_ends:
        for idx in range(max(len(phase_names), len(phase_starts), len(phase_ends))):
            name = (phase_names[idx].strip() if idx < len(phase_names) else "")
            start_raw = phase_starts[idx] if idx < len(phase_starts) else ""
            end_raw = phase_ends[idx] if idx < len(phase_ends) else ""
            if not (name or start_raw or end_raw):
                continue
            if not (name and start_raw and end_raw):
                return _render_settings_with_semester_error(request, "Each phase needs a name, start date, and end date.")
            try:
                from datetime import date as _date
                start = _date.fromisoformat(start_raw)
                end = _date.fromisoformat(end_raw)
            except Exception:
                return _render_settings_with_semester_error(request, "Invalid date format in semester phases.")
            if start > end:
                return _render_settings_with_semester_error(request, "Phase start must be on or before phase end.")
            phases.append({"name": name, "start": start.isoformat(), "end": end.isoformat()})

    if not phases:
        if not start_date_raw or not end_date_raw:
            return _render_settings_with_semester_error(request, "Please provide both start and end dates.")

        try:
            from datetime import date as _date
            start_date = _date.fromisoformat(start_date_raw)
            end_date = _date.fromisoformat(end_date_raw)
        except Exception:
            return _render_settings_with_semester_error(request, "Invalid date format.")

        if start_date > end_date:
            return _render_settings_with_semester_error(request, "Start date must be on or before end date.")

    semesters_per_year = None
    years_per_program = None
    if semesters_per_year_raw:
        try:
            semesters_per_year = int(semesters_per_year_raw)
        except ValueError:
            return _render_settings_with_semester_error(request, "Semesters per year must be a number.")
        if semesters_per_year <= 0:
            return _render_settings_with_semester_error(request, "Semesters per year must be greater than 0.")

    if years_per_program_raw:
        try:
            years_per_program = int(years_per_program_raw)
        except ValueError:
            return _render_settings_with_semester_error(request, "Years per program must be a number.")
        if years_per_program <= 0:
            return _render_settings_with_semester_error(request, "Years per program must be greater than 0.")

    phase_names = [p.strip() for p in phase_names_raw.split(",") if p.strip()]

    settings.semester_start_date = start_date if not phases else None
    settings.semester_end_date = end_date if not phases else None
    settings.semester_label = label if not phases else None
    settings.semesters_per_year = semesters_per_year
    settings.years_per_program = years_per_program
    settings.semester_phase_names = phase_names
    settings.semester_phases = phases
    settings.save()
    return redirect("core:settings")


@login_required
def password_change(request):
    if request.method != "POST":
        return redirect("core:settings")

    current_password = request.POST.get("current_password") or ""
    new_password = request.POST.get("new_password") or ""
    confirm_password = request.POST.get("confirm_password") or ""

    if not request.user.check_password(current_password):
        return _render_settings_with_password_error(request, "Current password is incorrect.")

    if not new_password or new_password != confirm_password:
        return _render_settings_with_password_error(request, "New passwords do not match.")

    request.user.set_password(new_password)
    request.user.save()
    update_session_auth_hash(request, request.user)
    return redirect("core:settings")


def _render_settings_with_password_error(request, error_message):
    settings, created = UserSettings.objects.get_or_create(user=request.user)
    semester = request.session.get("semester")
    week = request.session.get("week")
    if semester:
        setattr(settings, "semester", semester)
    if week:
        setattr(settings, "week", week)
    return render(request, "core/settings.html", {
        "settings": settings,
        "password_error": error_message,
        "open_password_modal": True,
    })


def _render_settings_with_semester_error(request, error_message):
    settings, created = UserSettings.objects.get_or_create(user=request.user)
    semester = request.session.get("semester")
    week = request.session.get("week")
    if semester:
        setattr(settings, "semester", semester)
    if week:
        setattr(settings, "week", week)
    return render(request, "core/settings.html", {
        "settings": settings,
        "semester_error": error_message,
        "open_semester_modal": True,
    })


@login_required
def logout_view(request):
    if request.method != "POST":
        return redirect("core:settings")
    auth_logout(request)
    return redirect("core:landing")
