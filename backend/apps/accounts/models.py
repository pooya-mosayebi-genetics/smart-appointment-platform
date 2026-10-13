import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
# ایمپورت تابع جدید تولید UUIDv7
from apps.core.utils import generate_uuid7


class Organization(models.Model):
    """
    نماینده بالاترین سطح مالکیت داده (Tenant).
    """
    id = models.UUIDField(primary_key=True, default=generate_uuid7, editable=False)
    name = models.CharField(max_length=255, verbose_name=_("نام سازمان"))
    slug = models.SlugField(unique=True, verbose_name=_("شناسه URL"))
    code = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name=_("کد سازمان"))
    
    STATUS_CHOICES = [
        ('active', _('فعال')),
        ('suspended', _('معلق')),
        ('inactive', _('غیرفعال')),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    timezone = models.CharField(max_length=50, default='Asia/Tehran', verbose_name=_("منطقه زمانی"))
    default_locale = models.CharField(max_length=10, default='fa-IR', verbose_name=_("زبان پیش‌فرض"))
    default_calendar = models.CharField(max_length=20, default='jalali', verbose_name=_("تقویم پیش‌فرض"))
    
    settings = models.JSONField(default=dict, blank=True, verbose_name=_("تنظیمات عمومی"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organizations'
        verbose_name = _("سازمان")
        verbose_name_plural = _("سازمان‌ها")

    def __str__(self):
        return self.name


class Branch(models.Model):
    """
    شعبه تحت یک سازمان.
    """
    id = models.UUIDField(primary_key=True, default=generate_uuid7, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='branches', verbose_name=_("سازمان"))
    
    name = models.CharField(max_length=255, verbose_name=_("نام شعبه"))
    code = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name=_("کد شعبه"))
    address = models.TextField(null=True, blank=True, verbose_name=_("آدرس"))
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name=_("تلفن"))
    
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    timezone = models.CharField(max_length=50, default='Asia/Tehran', verbose_name=_("منطقه زمانی"))
    
    STATUS_CHOICES = [
        ('active', _('فعال')),
        ('inactive', _('غیرفعال')),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    settings = models.JSONField(default=dict, blank=True, verbose_name=_("تنظیمات شعبه"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'branches'
        verbose_name = _("شعبه")
        verbose_name_plural = _("شعبه‌ها")
        constraints = [
            models.UniqueConstraint(fields=['organization', 'code'], name='unique_branch_code_per_org'),
        ]

    def __str__(self):
        return f"{self.organization.name} - {self.name}"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, mobile, password, **extra_fields):
        if not mobile:
            raise ValueError(_('The Mobile number must be set'))
        email = extra_fields.pop('email', None)
        user = self.model(mobile=mobile, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, mobile, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(mobile, password, **extra_fields)

    def create_superuser(self, mobile, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self._create_user(mobile, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    مدل سفارشی کاربر.
    """
    id = models.UUIDField(primary_key=True, default=generate_uuid7, editable=False)
    
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, related_name='users', verbose_name=_("سازمان"))
    
    mobile = models.CharField(max_length=20, unique=True, verbose_name=_("شماره موبایل"))
    email = models.EmailField(unique=True, null=True, blank=True, verbose_name=_("ایمیل"))
    
    first_name = models.CharField(max_length=100, blank=True, verbose_name=_("نام"))
    last_name = models.CharField(max_length=100, blank=True, verbose_name=_("نام خانوادگی"))
    
    national_id = models.CharField(max_length=20, null=True, blank=True, unique=True, verbose_name=_("کد ملی"))
    
    STATUS_CHOICES = [
        ('active', _('فعال')),
        ('inactive', _('غیرفعال')),
        ('blocked', _('مسدود شده')),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()

    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        verbose_name = _("کاربر")
        verbose_name_plural = _("کاربران")

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.mobile

    def __str__(self):
        return f"{self.get_full_name()} ({self.mobile})"


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=generate_uuid7, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='roles', verbose_name=_("سازمان"))
    
    name = models.CharField(max_length=100, verbose_name=("نام نقش"))
    code = models.CharField(max_length=50, unique=True, verbose_name=("کد نقش"))
    description = models.TextField(blank=True, verbose_name=("توضیحات"))
    
    is_system = models.BooleanField(default=False, help_text="نقش‌های سیستمی قابل حذف نیستند")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'roles'
        verbose_name = _("نقش")
        verbose_name_plural = _("نقش‌ها")

    def __str__(self):
        return self.name


class Permission(models.Model):
    id = models.UUIDField(primary_key=True, default=generate_uuid7, editable=False)
    code = models.CharField(max_length=100, unique=True, verbose_name=("کد دسترسی"))
    name = models.CharField(max_length=100, verbose_name=("نام دسترسی"))
    module = models.CharField(max_length=50, verbose_name=("ماژول مربوطه"))
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'permissions'
        verbose_name = _("دسترسی")
        verbose_name_plural = _("دسترسی‌ها")
        ordering = ['module', 'name']

    def __str__(self):
        return f"{self.module}: {self.name}"


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='permission_roles')
    
    class Meta:
        db_table = 'role_permissions'
        unique_together = ('role', 'permission')


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_users')
    
    class Meta:
        db_table = 'user_roles'
        unique_together = ('user', 'role')


class AccessScope(models.Model):
    id = models.UUIDField(primary_key=True, default=generate_uuid7, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_scopes')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='scope_roles')
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'access_scopes'
        verbose_name = _("دامنه دسترسی")
        verbose_name_plural = _("دامنه‌های دسترسی")

    def __str__(self):
        return f"{self.user.mobile} -> {self.role.code} in {self.branch.name if self.branch else 'All'}"