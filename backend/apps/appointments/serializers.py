from rest_framework import serializers
from .models import ServiceCategory, Service, Provider, ScheduleRule, AppointmentSlot


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ServiceSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Service
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProviderSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    service_names = serializers.StringRelatedField(many=True, source='services', read_only=True)

    class Meta:
        model = Provider
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return obj.get_full_name()


class ScheduleRuleSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = ScheduleRule
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class AppointmentSlotSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.get_full_name', read_only=True)

    class Meta:
        model = AppointmentSlot
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class BookAppointmentSerializer(serializers.ModelSerializer):
    """
    Serializer for booking an existing available slot.
    Only accepts patient info. Does not allow changing time/status directly.
    """
    class Meta:
        model = AppointmentSlot
        # فقط این دو فیلد توسط کاربر قابل نوشتن هستند
        fields = ['patient_mobile', 'patient_name'] 
        
    def validate_patient_mobile(self, value):
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("شماره موبایل معتبر نیست.")
        return value.strip()

    def validate_patient_name(self, value):
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("نام بیمار باید حداقل ۲ کاراکتر باشد.")
        return value.strip()