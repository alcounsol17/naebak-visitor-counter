import uuid
import hashlib
from datetime import datetime, timedelta
from flask import request, session
from src.models.visitor_counter import db, VisitorCounterSettings, VisitorSession, VisitorStats

class VisitorCounterService:
    """خدمة إدارة عداد الزوار"""
    
    @staticmethod
    def get_or_create_settings():
        """الحصول على إعدادات العداد أو إنشاؤها إذا لم تكن موجودة"""
        settings = VisitorCounterSettings.query.first()
        if not settings:
            settings = VisitorCounterSettings(
                min_base_count=1000,
                max_base_count=1500,
                current_base_count=1450,
                update_interval=30,
                is_active=True
            )
            db.session.add(settings)
            db.session.commit()
        return settings
    
    @staticmethod
    def update_settings(min_count, max_count, interval=30):
        """تحديث إعدادات العداد من قبل الأدمن"""
        settings = VisitorCounterService.get_or_create_settings()
        settings.min_base_count = min_count
        settings.max_base_count = max_count
        settings.update_interval = interval
        settings.updated_at = datetime.utcnow()
        
        # تحديث الرقم العشوائي فوراً بالإعدادات الجديدة
        settings.update_base_count()
        
        db.session.commit()
        return settings
    
    @staticmethod
    def get_current_base_count():
        """الحصول على الرقم العشوائي الحالي مع التحديث إذا لزم الأمر"""
        settings = VisitorCounterService.get_or_create_settings()
        
        if not settings.is_active:
            return 0
        
        # فحص ما إذا كان يجب تحديث الرقم العشوائي
        if settings.should_update():
            settings.update_base_count()
        
        return settings.current_base_count
    
    @staticmethod
    def generate_session_id():
        """إنشاء معرف جلسة فريد"""
        # استخدام IP + User Agent + timestamp لإنشاء معرف فريد
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
        user_agent = request.headers.get('User-Agent', '')
        timestamp = str(datetime.utcnow().timestamp())
        
        unique_string = f"{ip}_{user_agent}_{timestamp}_{uuid.uuid4()}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    @staticmethod
    def track_visitor():
        """تتبع زائر جديد أو تحديث زائر موجود"""
        # الحصول على معرف الجلسة من session أو إنشاء واحد جديد
        if 'visitor_session_id' not in session:
            session['visitor_session_id'] = VisitorCounterService.generate_session_id()
        
        session_id = session['visitor_session_id']
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
        user_agent = request.headers.get('User-Agent', '')
        
        # البحث عن الجلسة الموجودة
        visitor_session = VisitorSession.query.filter_by(session_id=session_id).first()
        
        if visitor_session:
            # تحديث الجلسة الموجودة
            visitor_session.update_activity()
        else:
            # إنشاء جلسة جديدة
            visitor_session = VisitorSession(
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                first_visit=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                page_views=1,
                is_active=True
            )
            db.session.add(visitor_session)
            db.session.commit()
        
        return visitor_session
    
    @staticmethod
    def get_active_visitors_count():
        """الحصول على عدد الزوار النشطين (خلال آخر 30 دقيقة)"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=30)
        active_count = VisitorSession.query.filter(
            VisitorSession.last_activity >= cutoff_time,
            VisitorSession.is_active == True
        ).count()
        
        return active_count
    
    @staticmethod
    def get_total_visitors_today():
        """الحصول على إجمالي الزوار اليوم"""
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        today_count = VisitorSession.query.filter(
            VisitorSession.first_visit >= today_start
        ).count()
        
        return today_count
    
    @staticmethod
    def get_displayed_visitor_count():
        """الحصول على العدد المعروض للزوار (الرقم العشوائي + الزوار الحقيقيون)"""
        base_count = VisitorCounterService.get_current_base_count()
        real_visitors = VisitorCounterService.get_active_visitors_count()
        
        displayed_count = base_count + real_visitors
        
        # تحديث إحصائيات اليوم
        VisitorCounterService.update_daily_stats(displayed_count)
        
        return displayed_count
    
    @staticmethod
    def update_daily_stats(displayed_count):
        """تحديث إحصائيات اليوم"""
        today = datetime.utcnow().date()
        
        stats = VisitorStats.query.filter_by(date=today).first()
        if not stats:
            stats = VisitorStats(
                date=today,
                unique_visitors=VisitorCounterService.get_total_visitors_today(),
                total_page_views=0,
                displayed_count=displayed_count
            )
            db.session.add(stats)
        else:
            stats.unique_visitors = VisitorCounterService.get_total_visitors_today()
            stats.displayed_count = displayed_count
            stats.updated_at = datetime.utcnow()
        
        # حساب إجمالي المشاهدات
        total_views = db.session.query(db.func.sum(VisitorSession.page_views)).filter(
            db.func.date(VisitorSession.first_visit) == today
        ).scalar() or 0
        
        stats.total_page_views = total_views
        db.session.commit()
        
        return stats
    
    @staticmethod
    def get_visitor_statistics():
        """الحصول على إحصائيات شاملة للزوار"""
        settings = VisitorCounterService.get_or_create_settings()
        active_visitors = VisitorCounterService.get_active_visitors_count()
        today_visitors = VisitorCounterService.get_total_visitors_today()
        displayed_count = VisitorCounterService.get_displayed_visitor_count()
        
        # إحصائيات آخر 7 أيام
        week_ago = datetime.utcnow().date() - timedelta(days=7)
        weekly_stats = VisitorStats.query.filter(
            VisitorStats.date >= week_ago
        ).order_by(VisitorStats.date.desc()).all()
        
        return {
            'settings': settings.to_dict(),
            'current_display_count': displayed_count,
            'active_visitors': active_visitors,
            'today_visitors': today_visitors,
            'base_count': settings.current_base_count,
            'weekly_stats': [stat.to_dict() for stat in weekly_stats]
        }
    
    @staticmethod
    def cleanup_old_sessions():
        """تنظيف الجلسات القديمة (أكثر من 24 ساعة)"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        old_sessions = VisitorSession.query.filter(
            VisitorSession.last_activity < cutoff_time
        ).all()
        
        for session_obj in old_sessions:
            session_obj.is_active = False
        
        db.session.commit()
        
        return len(old_sessions)
    
    @staticmethod
    def toggle_counter_status(is_active):
        """تفعيل أو إلغاء تفعيل العداد"""
        settings = VisitorCounterService.get_or_create_settings()
        settings.is_active = is_active
        settings.updated_at = datetime.utcnow()
        db.session.commit()
        
        return settings
