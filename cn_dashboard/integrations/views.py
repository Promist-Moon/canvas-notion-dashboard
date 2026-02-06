from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from core.models import UserSettings, SyncHistory

from .user import User


@require_POST
@login_required
def create_database(request):
	"""Create a Notion database using the tokens saved for the current user.

	Expects the current user to have `notion_token` and `canvas_token` saved and
	a `notion_page_id` specifying where to create the database.
	Returns JSON with {ok: True, database_id: ...} or an error.
	"""
	try:
		settings = UserSettings.objects.get(user=request.user)
	except UserSettings.DoesNotExist:
		return JsonResponse({"ok": False, "error": "No user settings found."}, status=400)

	notion_token = settings.notion_token
	canvas_token = settings.canvas_token
	page_id = settings.notion_page_id
	school_ab = settings.school_domain or ""

	if not notion_token or not canvas_token:
		SyncHistory.objects.create(
			user=request.user,
			action='create_db',
			status='error',
			error_messages=["Notion or Canvas token missing"]
		)
		return JsonResponse({"ok": False, "error": "Notion or Canvas token missing."}, status=400)

	if not page_id:
		SyncHistory.objects.create(
			user=request.user,
			action='create_db',
			status='error',
			error_messages=["Notion Page ID not set"]
		)
		return JsonResponse({"ok": False, "error": "Notion Page ID not set. Add it in Configure Secrets."}, status=400)

	try:
		user = User(canvas_token, notion_token, page_id, school_ab)
		new_db_id = user.createDatabase(properties=settings.db_properties)

		if new_db_id:
			settings.notion_database_id = new_db_id
			settings.save()
			SyncHistory.objects.create(
				user=request.user,
				action='create_db',
				status='success',
				database_id=new_db_id
			)
			return JsonResponse({"ok": True, "database_id": new_db_id})
		else:
			SyncHistory.objects.create(
				user=request.user,
				action='create_db',
				status='error',
				error_messages=["No database id returned from Notion"]
			)
			return JsonResponse({"ok": False, "error": "No database id returned from Notion."}, status=500)
	except Exception as e:
		SyncHistory.objects.create(
			user=request.user,
			action='create_db',
			status='error',
			error_messages=[str(e)]
		)
		return JsonResponse({"ok": False, "error": str(e)}, status=500)
