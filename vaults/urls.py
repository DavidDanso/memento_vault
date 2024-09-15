from django.urls import path
from . import views

urlpatterns = [
    path('party/911/', views.uploads_view, name='uploads'),
]