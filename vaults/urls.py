from django.urls import path
from . import views

urlpatterns = [
    path('', views.vault_view, name='vaults'),
    path('<uuid:pk>/<str:title>', views.vault_details_view, name='vault-details'),
]