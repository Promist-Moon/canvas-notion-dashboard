from django.shortcuts import render, redirect
from .models import UserSettings

def landing(request):
    if request.user.is_authenticated:
        settings, created = UserSettings.objects.get_or_create(user=request.user)
        return render(request, "core/home.html", {
            'db_properties': settings.db_properties
        })
    return render(request, "core/welcome.html")

def configure_secrets(request):
    if request.method == "POST":
        n_token = request.POST.get('notion_token')
        c_token = request.POST.get('canvas_token')
        sch = request.POST.get('school_domain')
        
        # Save to database
        settings, created = UserSettings.objects.get_or_create(user=request.user)
        settings.notion_token = n_token
        settings.canvas_token = c_token
        settings.school_domain = sch
        settings.save()
        
        return redirect('core:landing')

def save_db_settings(request):
    if request.method == "POST":
        selected_props = request.POST.getlist('properties')
        
        settings = UserSettings.objects.get(user=request.user)
        settings.db_properties = selected_props
        settings.save()
        
        return redirect('core:landing')
