from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from vaults.views import *
from a_auth.views import *


urlpatterns = [
    # admin
    path('admin/', admin.site.urls),

    # user
    path('profile', include('users.urls')),

    # vault
    path('vaults/', include('vaults.urls')),
    path('dashboard', dashboard_view, name='dashboard'),
    path('user-uploads/<uuid:vault_id>', uploads_view, name='uploads'),
    path('download-qr/<uuid:vault_id>/', download_qr_code, name='download-qr'),
    path('thank_u', thankY_view, name='thank_u'),
    path('everything', everything_view, name='everything'),
    path('gallery', gallery_view, name='gallery'),

    # auth
    path('login', login_view, name='login'),
    path('sign-up', signup_view, name='sign-up'),
    path('logout', logout_view, name='logout'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Change Site Title, Index Title and Site Title
admin.site.site_header = "Memento Vault Panel"
admin.site.site_title = "Memento Vault Panel"
admin.site.index_title = "Welcome to Memento Vault Panel"