from django.urls import path
from . import views

urlpatterns = [
    path('911/', views.vault_view, name='vault-details'),
]