from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ServiceCategoryViewSet, 
    ServiceViewSet, 
    ProviderViewSet, 
    ScheduleRuleViewSet,
    AppointmentSlotViewSet,
    generate_slots_view,
    BookAppointmentView
)

router = DefaultRouter()
router.register(r'categories', ServiceCategoryViewSet, basename='service-category')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'providers', ProviderViewSet, basename='provider')
router.register(r'schedules', ScheduleRuleViewSet, basename='schedule-rule')
router.register(r'slots', AppointmentSlotViewSet, basename='appointment-slot')

urlpatterns = [
    path('', include(router.urls)),
    
    # مسیر اختصاصی برای تولید اسلات
    path('providers/<uuid:provider_id>/generate-slots/', generate_slots_view, name='generate-provider-slots'),
    
    # مسیر جدید برای رزرو نوبت
    path('slots/<uuid:pk>/book/', BookAppointmentView.as_view(), name='book-appointment'),
]