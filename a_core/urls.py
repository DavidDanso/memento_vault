from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from vaults.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('profile/', include('users.urls')),
    path('vaults/', include('vaults.urls')),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('user-uploads/911/', uploads_view, name='uploads'),
    path('thank_u/', thankY_view, name='thank_u'),
    path('everything/', everything_view, name='everything'),
]

# Only used when DEBUG=True, whitenoise can serve files when DEBUG=False
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Change Site Title, Index Title and Site Title
admin.site.site_header = "Memento Vault Panel"
admin.site.site_title = "Memento Vault Panel"
admin.site.index_title = "Welcome to Memento Vault Panel"