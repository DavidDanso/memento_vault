from django.shortcuts import render
from django.contrib.auth.decorators import login_required


# 
@login_required(login_url='login')
def dashboard_view(request):
    context = {}
    return render(request, 'dashboard.html', context)


# 
def vault_view(request):
    context = {}
    return render(request, 'vaults/vaults.html', context)


# 
def vault_details_view(request):
    context = {}
    return render(request, 'vaults/vault_details.html', context)


# 
def everything_view(request):
    context = {}
    return render(request, 'vaults/everything.html', context)


# 
def gallery_view(request):
    context = {}
    return render(request, 'vaults/gallery.html', context)


# 
def thankY_view(request):
    context = {}
    return render(request, 'thankY_page.html', context)


# 
def uploads_view(request):
    context = {}
    return render(request, 'vaults/uploads_page.html', context)