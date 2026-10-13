from datetime import datetime, timedelta, time
from django.db import transaction
from .models import Provider, ScheduleRule, Service, AppointmentSlot


class SlotGenerationService:
    """
    سرویسی برای تولید اسلات‌های نوبت بر اساس قوانین برنامه پزشکان.
    """
    
    @staticmethod
    def generate_slots_for_provider(provider_id: str, start_date: datetime, days_ahead: int = 7):
        """
        تولید اسلات‌ها برای یک پزشک خاص در بازه زمانی مشخص.
        
        Args:
            provider_id: UUID پزشک
            start_date: تاریخ شروع محاسبه (مثلاً امروز)
            days_ahead: چند روز آینده را پوشش دهیم
            
        Returns:
            تعداد اسلات‌های ساخته شده
        """
        try:
            provider = Provider.objects.get(id=provider_id)
        except Provider.DoesNotExist:
            raise ValueError("پزشک یافت نشد.")

        # دریافت قوانین برنامه پزشک
        schedule_rules = ScheduleRule.objects.filter(provider=provider)
        
        if not schedule_rules.exists():
            return 0

        generated_count = 0
        
        # حلقه روی روزهای مورد نظر
        current_date = start_date.date()
        end_date = current_date + timedelta(days=days_ahead)
        
        while current_date <= end_date:
            # day_of_week در جنگو: 0=Monday, ..., 6=Sunday
            # اما در مدل ما تعریف کردیم: 0=Saturday, 1=Sunday...
            # پس باید تبدیل کنیم.
            # Python weekday(): Mon=0, Sun=6
            # Our Model: Sat=0, Sun=1, Mon=2 ... Fri=6
            
            py_weekday = current_date.weekday() # 0=Mon, 6=Sun
            
            # تبدیل به فرمت مدل ما (Sat=0)
            # Mapping from Python weekday to our custom enum
            # Python: Mon(0), Tue(1), Wed(2), Thu(3), Fri(4), Sat(5), Sun(6)
            # Custom: Sat(0), Sun(1), Mon(2), Tue(3), Wed(4), Thu(5), Fri(6)
            
            custom_day_map = {
                5: 0, # Sat
                6: 1, # Sun
                0: 2, # Mon
                1: 3, # Tue
                2: 4, # Wed
                3: 5, # Thu
                4: 6, # Fri
            }
            
            target_custom_day = custom_day_map[py_weekday]
            
            # پیدا کردن قوانین مربوط به این روز
            daily_rules = schedule_rules.filter(day_of_week=target_custom_day)
            
            for rule in daily_rules:
                if rule.is_break_time:
                    continue
                
                # تولید اسلات‌ها برای این بازه زمانی
                slots_created = SlotGenerationService._create_slots_from_rule(
                    provider=provider,
                    rule=rule,
                    date=current_date
                )
                generated_count += slots_created
                
            current_date += timedelta(days=1)
            
        return generated_count

    @staticmethod
    def _create_slots_from_rule(provider, rule, date):
        """
        کمک‌تابع برای تقسیم یک بازه زمانی به اسلات‌های کوچکتر.
        """
        count = 0
        start_dt = datetime.combine(date, rule.start_time)
        end_dt = datetime.combine(date, rule.end_time)
        duration = timedelta(minutes=rule.slot_duration_minutes)
        
        current_slot_start = start_dt
        
        with transaction.atomic():
            while current_slot_start < end_dt:
                slot_end = current_slot_start + duration
                
                # اگر اسلات از پایان وقت اداری عبور کرد، قطع کن
                if slot_end > end_dt:
                    break
                
                # بررسی اینکه آیا این اسلات قبلاً ساخته شده یا نه (Idempotency)
                exists = AppointmentSlot.objects.filter(
                    provider=provider,
                    date=date,
                    start_time=current_slot_start.time()
                ).exists()
                
                if not exists:
                    AppointmentSlot.objects.create(
                        provider=provider,
                        date=date,
                        start_time=current_slot_start.time(),
                        end_time=slot_end.time(),
                        status='available'
                    )
                    count += 1
                    
                current_slot_start = slot_end
                
        return count