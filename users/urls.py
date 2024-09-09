from django.urls import path
from users.views import *

urlpatterns = [
    path('', profile_view, name="profile"),
]