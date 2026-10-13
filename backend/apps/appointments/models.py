import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.utils import generate_uuid7
from apps.accounts.models import Organization, Branch


class ServiceCategory(models.Model):
    """
    دسته‌بندی خدمات (مثلاً: پزشکی، دندانپزشکی، زیبایی)
    """
    id = models.UUIDField(primary_key=True, default=generate_uuid7, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='service_categories')
    
    name = models.CharField(max_length=100, verbose_name=_("نام دسته"))
    slug = models.SlugField(verbose_name=("شناسه URL"))
    description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'service_categories'
        unique_together = ('organization', 'slug')
        verbose_name = _("دسته‌بندی خدمت")
        verbose_name_plural = _("دسته‌بندی‌های خدمت")

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class Service(models.Model):
    """
    خدمت قابل ارائه (مثلاً: ویزیت متخصص قلب)
    """
    id = models.UUIDField(primary_key=True, default=generate_uuid7, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='services')
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='services')
    
    name = models.CharField(max_length=255, verbose_name=_("نام خدمت"))
    code = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name=_("کد خدمت"))
    description = models.TextField(blank=True, null=True, verbose_name=_("توضیحات"))
    
    duration_minutes = models.PositiveIntegerField(default=15, verbose_name=_("مدت زمان (دقیقه)"))
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("قیمت"))
    
    STATUS_CHOICES = [
        ('active', _('فعال')),
        ('inactive', _('غیرفعال')),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    requires_prescription = models.BooleanField(default=False, verbose_name=_("نیاز به نسخه دارد؟"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'services'
        verbose_name = _("خدمت")
        verbose_name_plural = _("خدمات")
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.name


class Provider(models.Model):
    """
    ارائه‌دهنده خدمت (پزشک، پرستار، تکنسین)
    """
    id = models.UUIDField(primary_key=True, default=generate_uuid7, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='providers')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='providers', null=True, blank=True)
    
    # ارتباط با کاربر سیستم (Optional: اگر پزشک هم اکانت لاگین داشته باشد)
    user = models.OneToOneField('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='provider_profile')
    
    first_name = models.CharField(max_length=100, verbose_name=_("نام"))
    last_name = models.CharField(max_length=100, verbose_name=_("نام خانوادگی"))
    
    national_id = models.CharField(max_length=20, null=True, blank=True, verbose_name=_("کد ملی"))
    license_number = models.CharField(max_length=50, null=True, blank=True, verbose_name=_("شماره نظام پزشکی"))
    
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name=_("تلفن تماس"))
    email = models.EmailField(null=True, blank=True, verbose_name=_("ایمیل"))
    
    bio = models.TextField(blank=True, null=True, verbose_name=_("بیوگرافی"))
    photo_url = models.URLField(blank=True, null=True, verbose_name=_("آدرس عکس"))
    
    services = models.ManyToManyField(Service, related_name='providers', blank=True, verbose_name=_("خدمات ارائه شده"))
    
    STATUS_CHOICES = [
        ('active', _('فعال')),
        ('on_leave', _('مرخصی')),
        ('inactive', _('غیرفعال')),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'providers'
        verbose_name = _("ارائه‌دهنده")
        verbose_name_plural = _("ارائه‌دهندگان")
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
        ]

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"Dr./Mr./Ms. {self.get_full_name()}"


class ScheduleRule(models.Model):
    """
    قوانین برنامه هفتگی ارائه‌دهنده
    مثال: هر شنبه و چهارشنبه، ساعت 9 تا 13 و 15 تا 18
    """
    id = models.UUIDField(primary_key=True, default=generate_uuid7, editable=False)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='schedule_rules')
    
    DAY_OF_WEEK_CHOICES = [
        (0, _('شنبه')),
        (1, _('یکشنبه')),
        (2, _('دوشنبه')),
        (3, _('سه‌شنبه')),
        (4, _('چهارشنبه')),
        (5, _('پنجشنبه')),
        (6, _('جمعه')),
    ]
    day_of_week = models.IntegerField(choices=DAY_OF_WEEK_CHOICES, verbose_name=_("روز هفته"))
    
    start_time = models.TimeField(verbose_name=_("ساعت شروع"))
    end_time = models.TimeField(verbose_name=_("ساعت پایان"))
    
    slot_duration_minutes = models.PositiveIntegerField(default=15, verbose_name=_("طول هر اسلات (دقیقه)"))
    
    is_break_time = models.BooleanField(default=False, help_text="اگر True باشد، این بازه استراحت تلقی می‌شود و نوبت گرفته نمی‌شود")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'schedule_rules'
        verbose_name = _("قانون برنامه")
        verbose_name_plural = _("قوانین برنامه")
        constraints = [
            models.UniqueConstraint(fields=['provider', 'day_of_week', 'start_time'], name='unique_schedule_slot'),
        ]
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        days = dict(self.DAY_OF_WEEK_CHOICES)[self.day_of_week]
        return f"{days}: {self.start_time} - {self.end_time} for {self.provider.get_full_name()}"


class AppointmentSlot(models.Model):
    """
    نماینده یک بازه زمانی مشخص برای یک ارائه‌دهنده.
    این رکوردها معمولاً توسط سرویس SlotGenerator به صورت خودکار ساخته می‌شوند.
    """
    id = models.UUIDField(primary_key=True, default=generate_uuid7, editable=False)
    
    # ارتباطات
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='slots')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='slots', null=True, blank=True)
    
    # زمان اسلات
    date = models.DateField(verbose_name=_("تاریخ"))
    start_time = models.TimeField(verbose_name=_("ساعت شروع"))
    end_time = models.TimeField(verbose_name=_("ساعت پایان"))
    
    # وضعیت
    STATUS_CHOICES = [
        ('available', _('آزاد')),
        ('booked', _('رزرو شده')),
        ('cancelled', _('لغو شده')),
        ('blocked', _('مسدود/مرخصی')),
    ]
    # ⬇️ تغییر مهم: حذف index=True از اینجا
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    
    # اطلاعات رزرو (اگر booked باشد)
    patient_mobile = models.CharField(max_length=20, null=True, blank=True, verbose_name=_("موبایل بیمار"))
    patient_name = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("نام بیمار"))
    booking_reference = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name=_("کد رهگیری"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'appointment_slots'
        verbose_name = _("اسلات نوبت")
        verbose_name_plural = _("اسلات‌های نوبت")
        # جلوگیری از تداخل زمانی: یک پزشک نمی‌تواند دو اسلات با همپوشانی زمانی در یک روز داشته باشد
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'date', 'start_time'], 
                name='unique_provider_slot_time'
            ),
        ]
        ordering = ['date', 'start_time']
        
        # ⬇️ تغییر مهم: اضافه کردن ایندکس از طریق Meta
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['provider', 'date']), # برای کوئری‌های سریع لیست نوبت‌های یک دکتر در یک روز
        ]

    def __str__(self):
        return f"{self.provider.get_full_name()} - {self.date} {self.start_time}-{self.end_time} ({self.status})"