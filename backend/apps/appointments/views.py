from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import GenericAPIView
from django.db import transaction
import uuid
from datetime import datetime

from .models import ServiceCategory, Service, Provider, ScheduleRule, AppointmentSlot
from .serializers import (
    ServiceCategorySerializer, 
    ServiceSerializer, 
    ProviderSerializer, 
    ScheduleRuleSerializer,
    AppointmentSlotSerializer,
    BookAppointmentSerializer
)
from .services import SlotGenerationService


# --- Standard ViewSets ---

class ServiceCategoryViewSet(viewsets.ModelViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [IsAuthenticated]


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.select_related('category').all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]


class ProviderViewSet(viewsets.ModelViewSet):
    queryset = Provider.objects.prefetch_related('services').select_related('branch').all()
    serializer_class = ProviderSerializer
    
    # ⬇️ تغییر مهم: فقط برای GET و HEAD عمومی باشد، برای CREATE/UPDATE/DELETE لاگین لازم است
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]


class ScheduleRuleViewSet(viewsets.ModelViewSet):
    queryset = ScheduleRule.objects.select_related('provider').all()
    serializer_class = ScheduleRuleSerializer
    permission_classes = [IsAuthenticated]


class AppointmentSlotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    فقط اجازه مشاهده اسلات‌ها را می‌دهد (برای بیمار).
    """
    queryset = AppointmentSlot.objects.select_related('provider').all()
    serializer_class = AppointmentSlotSerializer
    permission_classes = [AllowAny] # عمومی برای دیدن نوبت‌های آزاد
    
    def get_queryset(self):
        qs = super().get_queryset()
        provider_id = self.request.query_params.get('provider')
        date_str = self.request.query_params.get('date')
        
        if provider_id:
            qs = qs.filter(provider_id=provider_id)
        if date_str:
            qs = qs.filter(date=date_str)
            
        return qs.order_by('date', 'start_time')


# --- Special Action Views ---

@api_view(['POST'])
@permission_classes([IsAuthenticated]) # فقط کاربران لاگین کرده (ادمین/پزشک)
def generate_slots_view(request, provider_id):
    """
    Endpoint to trigger slot generation for a specific provider.
    POST /api/v1/appointments/providers/{id}/generate-slots/
    Body: { "start_date": "YYYY-MM-DD", "days_ahead": 7 }
    """
    try:
        start_date_str = request.data.get('start_date')
        days_ahead = int(request.data.get('days_ahead', 7))
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.now()
            
        count = SlotGenerationService.generate_slots_for_provider(
            provider_id=str(provider_id),
            start_date=start_date,
            days_ahead=days_ahead
        )
        
        return Response({
            "message": f"تولید اسلات‌ها با موفقیت انجام شد.",
            "generated_count": count
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BookAppointmentView(GenericAPIView):
    """
    Endpoint to book a specific appointment slot.
    PATCH /api/v1/appointments/slots/{id}/book/
    Body: { "patient_mobile": "...", "patient_name": "..." }
    """
    serializer_class = BookAppointmentSerializer
    permission_classes = [AllowAny] # در نسخه نهایی باید محدود شود، فعلاً آزاد
    
    def patch(self, request, pk):
        # ۱. پیدا کردن اسلات مورد نظر
        try:
            slot = AppointmentSlot.objects.get(id=pk)
        except AppointmentSlot.DoesNotExist:
            return Response({"error": "اسلات یافت نشد."}, status=status.HTTP_404_NOT_FOUND)

        # ۲. بررسی اولیه وضعیت اسلات (قبل از شروع تراکنش سنگین)
        if slot.status != 'available':
            return Response({
                "error": "این نوبت قبلاً رزرو شده یا مسدود است.",
                "current_status": slot.status
            }, status=status.HTTP_409_CONFLICT)

        # ۳. اعتبارسنجی داده‌های ورودی
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # ۴. به‌روزرسانی اسلات در یک Transaction (برای جلوگیری از خطا در حالت همزمانی)
        with transaction.atomic():
            # قفل کردن ردیف در دیتابیس تا دیگری نتواند همزمان تغییر دهد (Select For Update)
            # این مهم‌ترین بخش برای سیستم نوبت‌دهی است
            locked_slot = AppointmentSlot.objects.select_for_update().get(id=pk)
            
            # دوباره چک کنیم که آیا هنوز آزاد است؟ (ممکن است بین مرحله ۲ و ۴ کسی دیگر آن را گرفته باشد)
            if locked_slot.status != 'available':
                 return Response({
                    "error": "متأسفانه همین لحظه این نوبت توسط شخص دیگری رزرو شد.",
                }, status=status.HTTP_409_CONFLICT)

            # اعمال تغییرات
            locked_slot.patient_mobile = serializer.validated_data['patient_mobile']
            locked_slot.patient_name = serializer.validated_data['patient_name']
            locked_slot.status = 'booked'
            # تولید کد رهگیری یکتا (مثلاَ BK-A1B2C3D4)
            locked_slot.booking_reference = f"BK-{uuid.uuid4().hex[:8].upper()}" 
            locked_slot.save()

        # ۵. برگرداندن پاسخ موفق
        output_serializer = AppointmentSlotSerializer(locked_slot)
        return Response(output_serializer.data, status=status.HTTP_200_OK)