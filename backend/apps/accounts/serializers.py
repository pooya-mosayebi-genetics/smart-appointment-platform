from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import Organization, Branch


class LoginSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=20, required=True)
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=True)

    def validate(self, attrs):
        mobile = attrs.get('mobile')
        password = attrs.get('password')

        if not mobile or not password:
            raise serializers.ValidationError("لطفاً شماره موبایل و رمز عبور را وارد کنید.")

        user = authenticate(request=self.context.get('request'), username=mobile, password=password)

        if not user:
            msg = 'شماره موبایل یا رمز عبور اشتباه است.'
            raise serializers.ValidationError(msg, code='authorization')

        if not user.is_active:
            msg = 'این حساب کاربری غیرفعال است.'
            raise serializers.ValidationError(msg, code='inactive')

        attrs['user'] = user
        return attrs


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug', 'code', 'status', 'timezone', 'default_locale', 'default_calendar', 'settings', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class BranchSerializer(serializers.ModelSerializer):
    organization_name = serializers.ReadOnlyField(source='organization.name') # نمایش نام سازمان والد

    class Meta:
        model = Branch
        fields = ['id', 'organization', 'organization_name', 'name', 'code', 'address', 'phone', 'latitude', 'longitude', 'timezone', 'status', 'settings', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']