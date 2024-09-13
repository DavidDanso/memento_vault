from django.urls import path
from . import views

urlpatterns = [
    path('vault_name/18266272728829339019e37/', views.uploads_view, name='uploads'),
]