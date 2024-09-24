from django.shortcuts import render


# 
def dashboard_view(request):
    context = {}
    return render(request, 'dashboard.html', context)


# 
def vault_view(request):
    context = {}
    return render(request, 'vaults/vault_details.html', context)


# 
def everything_view(request):
    context = {}
    return render(request, 'vaults/everything.html', context)


# 
def thankY_view(request):
    context = {}
    return render(request, 'thankY_page.html', context)


# 
def uploads_view(request):
    context = {}
    return render(request, 'vaults/uploads_page.html', context)