from django.shortcuts import render

# 
def thankY_view(request):
    context = {}
    return render(request, 'thankY_page.html', context)


# 
def uploads_view(request):
    context = {}
    return render(request, 'vaults/uploads_page.html', context)