from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health Check
    path('api/', include('apps.core.urls')), 
    
    # Auth & Resources under v1
    path('api/v1/auth/', include('apps.accounts.urls')),
    
    # Appointments Module
    path('api/v1/appointments/', include('apps.appointments.urls')), 
]