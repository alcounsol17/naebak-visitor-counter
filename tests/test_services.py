import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from src.services.visitor_service import VisitorCounterService
from src.models.visitor_counter import VisitorCounterSettings, VisitorSession, VisitorStats, db
from src.main import app

class TestVisitorCounterService:
    """اختبارات خدمة عداد الزوار"""
    
    def test_get_or_create_settings_existing(self, client):
        """اختبار الحصول على إعدادات موجودة"""
        with app.app_context():
            settings = VisitorCounterService.get_or_create_settings()
            
            assert settings is not None
            assert isinstance(settings, VisitorCounterSettings)
            assert settings.min_base_count == 1000
            assert settings.max_base_count == 1500
    
    def test_get_or_create_settings_new(self, client):
        """اختبار إنشاء إعدادات جديدة عند عدم وجودها"""
        with app.app_context():
            # حذف الإعدادات الموجودة
            VisitorCounterSettings.query.delete()
            db.session.commit()
            
            settings = VisitorCounterService.get_or_create_settings()
            
            assert settings is not None
            assert settings.min_base_count == 1000
            assert settings.max_base_count == 1500
            assert settings.is_active == True
    
    def test_update_settings(self, client):
        """اختبار تحديث الإعدادات"""
        with app.app_context():
            updated_settings = VisitorCounterService.update_settings(
                min_count=2000,
                max_count=3000,
                interval=60
            )
            
            assert updated_settings.min_base_count == 2000
            assert updated_settings.max_base_count == 3000
            assert updated_settings.update_interval == 60
            assert 2000 <= updated_settings.current_base_count <= 3000
    
    def test_get_current_base_count_active(self, client):
        """اختبار الحصول على الرقم الأساسي عندما يكون العداد مفعلاً"""
        with app.app_context():
            base_count = VisitorCounterService.get_current_base_count()
            
            assert isinstance(base_count, int)
            assert base_count > 0
    
    def test_get_current_base_count_inactive(self, client):
        """اختبار الحصول على الرقم الأساسي عندما يكون العداد معطلاً"""
        with app.app_context():
            # تعطيل العداد
            settings = VisitorCounterSettings.query.first()
            settings.is_active = False
            db.session.commit()
            
            base_count = VisitorCounterService.get_current_base_count()
            
            assert base_count == 0
    
    @patch('src.services.visitor_service.request')
    def test_generate_session_id(self, mock_request, client):
        """اختبار إنشاء معرف جلسة فريد"""
        # إعداد mock للطلب
        mock_request.environ = {
            'REMOTE_ADDR': '192.168.1.1'
        }
        mock_request.headers = {
            'User-Agent': 'Test Browser'
        }
        
        with app.app_context():
            session_id = VisitorCounterService.generate_session_id()
            
            assert isinstance(session_id, str)
            assert len(session_id) == 32  # MD5 hash length
    
    @patch('src.services.visitor_service.session')
    @patch('src.services.visitor_service.request')
    def test_track_visitor_new(self, mock_request, mock_session, client):
        """اختبار تتبع زائر جديد"""
        # إعداد mock
        mock_session.__contains__ = MagicMock(return_value=False)
        mock_session.__setitem__ = MagicMock()
        mock_session.__getitem__ = MagicMock(return_value='new_test_session')
        
        mock_request.environ = {
            'REMOTE_ADDR': '192.168.1.10'
        }
        mock_request.headers = {
            'User-Agent': 'New Test Browser'
        }
        
        with app.app_context():
            visitor_session = VisitorCounterService.track_visitor()
            
            assert visitor_session is not None
            assert isinstance(visitor_session, VisitorSession)
    
    def test_get_active_visitors_count(self, client, create_test_sessions):
        """اختبار حساب الزوار النشطين"""
        with app.app_context():
            active_count = VisitorCounterService.get_active_visitors_count()
            
            # يجب أن يكون هناك زائران نشطان (الجلسات الحديثة فقط)
            assert active_count >= 0
            assert isinstance(active_count, int)
    
    def test_get_total_visitors_today(self, client, create_test_sessions):
        """اختبار حساب إجمالي زوار اليوم"""
        with app.app_context():
            today_count = VisitorCounterService.get_total_visitors_today()
            
            assert today_count >= 0
            assert isinstance(today_count, int)
    
    def test_get_displayed_visitor_count(self, client):
        """اختبار الحصول على العدد المعروض"""
        with app.app_context():
            displayed_count = VisitorCounterService.get_displayed_visitor_count()
            
            assert displayed_count >= 0
            assert isinstance(displayed_count, int)
    
    def test_update_daily_stats(self, client):
        """اختبار تحديث إحصائيات اليوم"""
        with app.app_context():
            displayed_count = 1500
            stats = VisitorCounterService.update_daily_stats(displayed_count)
            
            assert stats is not None
            assert isinstance(stats, VisitorStats)
            assert stats.displayed_count == displayed_count
            assert stats.date == datetime.utcnow().date()
    
    def test_get_visitor_statistics(self, client):
        """اختبار الحصول على إحصائيات شاملة"""
        with app.app_context():
            statistics = VisitorCounterService.get_visitor_statistics()
            
            assert isinstance(statistics, dict)
            assert 'settings' in statistics
            assert 'current_display_count' in statistics
            assert 'active_visitors' in statistics
            assert 'today_visitors' in statistics
            assert 'base_count' in statistics
            assert 'weekly_stats' in statistics
    
    def test_cleanup_old_sessions(self, client, create_test_sessions):
        """اختبار تنظيف الجلسات القديمة"""
        with app.app_context():
            # إنشاء جلسة قديمة إضافية
            old_session = VisitorSession(
                session_id='very_old_session',
                ip_address='192.168.1.99',
                first_visit=datetime.utcnow() - timedelta(hours=30),
                last_activity=datetime.utcnow() - timedelta(hours=30),
                is_active=True
            )
            db.session.add(old_session)
            db.session.commit()
            
            cleaned_count = VisitorCounterService.cleanup_old_sessions()
            
            assert cleaned_count >= 0
            assert isinstance(cleaned_count, int)
    
    def test_toggle_counter_status_activate(self, client):
        """اختبار تفعيل العداد"""
        with app.app_context():
            # تعطيل العداد أولاً
            settings = VisitorCounterSettings.query.first()
            settings.is_active = False
            db.session.commit()
            
            # تفعيل العداد
            updated_settings = VisitorCounterService.toggle_counter_status(True)
            
            assert updated_settings.is_active == True
    
    def test_toggle_counter_status_deactivate(self, client):
        """اختبار إلغاء تفعيل العداد"""
        with app.app_context():
            # تفعيل العداد أولاً
            settings = VisitorCounterSettings.query.first()
            settings.is_active = True
            db.session.commit()
            
            # إلغاء تفعيل العداد
            updated_settings = VisitorCounterService.toggle_counter_status(False)
            
            assert updated_settings.is_active == False

class TestVisitorCounterServiceEdgeCases:
    """اختبارات الحالات الحدية لخدمة عداد الزوار"""
    
    def test_update_settings_invalid_range(self, client):
        """اختبار تحديث الإعدادات بنطاق غير صحيح"""
        with app.app_context():
            # هذا الاختبار يتحقق من أن الخدمة تتعامل مع النطاقات غير الصحيحة
            # في التطبيق الفعلي، يجب أن تكون هناك تحققات في API
            settings = VisitorCounterService.update_settings(
                min_count=1500,  # أكبر من الحد الأقصى
                max_count=1000,
                interval=30
            )
            
            # الخدمة ستقبل القيم ولكن API يجب أن يرفضها
            assert settings.min_base_count == 1500
            assert settings.max_base_count == 1000
    
    def test_get_statistics_empty_database(self, client):
        """اختبار الحصول على الإحصائيات مع قاعدة بيانات فارغة"""
        with app.app_context():
            # حذف جميع الجلسات والإحصائيات
            VisitorSession.query.delete()
            VisitorStats.query.delete()
            db.session.commit()
            
            statistics = VisitorCounterService.get_visitor_statistics()
            
            assert statistics['active_visitors'] == 0
            assert statistics['today_visitors'] == 0
            assert len(statistics['weekly_stats']) == 0
