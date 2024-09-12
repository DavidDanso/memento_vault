from django.shortcuts import render

# Create your views here.
def thankY_view(request):
    context = {}
    return render(request, 'thankY_page.html', context)