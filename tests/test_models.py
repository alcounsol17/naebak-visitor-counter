import pytest
from datetime import datetime, timedelta
from src.models.visitor_counter import VisitorCounterSettings, VisitorSession, VisitorStats, db
from src.main import app

class TestVisitorCounterSettings:
    """اختبارات نموذج إعدادات عداد الزوار"""
    
    def test_create_settings(self, client):
        """اختبار إنشاء إعدادات جديدة"""
        with app.app_context():
            settings = VisitorCounterSettings(
                min_base_count=500,
                max_base_count=1000,
                update_interval=45
            )
            db.session.add(settings)
            db.session.commit()
            
            assert settings.id is not None
            assert settings.min_base_count == 500
            assert settings.max_base_count == 1000
            assert settings.update_interval == 45
            assert settings.is_active == True  # القيمة الافتراضية
    
    def test_update_base_count(self, client):
        """اختبار تحديث الرقم العشوائي الأساسي"""
        with app.app_context():
            settings = VisitorCounterSettings.query.first()
            old_count = settings.current_base_count
            old_update_time = settings.last_update
            
            new_count = settings.update_base_count()
            
            assert new_count != old_count
            assert settings.min_base_count <= new_count <= settings.max_base_count
            assert settings.last_update > old_update_time
    
    def test_should_update_true(self, client):
        """اختبار أن العداد يحتاج للتحديث"""
        with app.app_context():
            settings = VisitorCounterSettings.query.first()
            # تعديل وقت آخر تحديث ليكون قديماً
            settings.last_update = datetime.utcnow() - timedelta(seconds=35)
            settings.update_interval = 30
            db.session.commit()
            
            assert settings.should_update() == True
    
    def test_should_update_false(self, client):
        """اختبار أن العداد لا يحتاج للتحديث"""
        with app.app_context():
            settings = VisitorCounterSettings.query.first()
            # تعديل وقت آخر تحديث ليكون حديثاً
            settings.last_update = datetime.utcnow() - timedelta(seconds=10)
            settings.update_interval = 30
            db.session.commit()
            
            assert settings.should_update() == False
    
    def test_to_dict(self, client):
        """اختبار تحويل الإعدادات إلى قاموس"""
        with app.app_context():
            settings = VisitorCounterSettings.query.first()
            data = settings.to_dict()
            
            assert isinstance(data, dict)
            assert 'id' in data
            assert 'min_base_count' in data
            assert 'max_base_count' in data
            assert 'current_base_count' in data
            assert 'is_active' in data

class TestVisitorSession:
    """اختبارات نموذج جلسة الزائر"""
    
    def test_create_visitor_session(self, client):
        """اختبار إنشاء جلسة زائر جديدة"""
        with app.app_context():
            session = VisitorSession(
                session_id='test_session_123',
                ip_address='192.168.1.100',
                user_agent='Test Browser',
                page_views=1
            )
            db.session.add(session)
            db.session.commit()
            
            assert session.id is not None
            assert session.session_id == 'test_session_123'
            assert session.ip_address == '192.168.1.100'
            assert session.page_views == 1
            assert session.is_active == True
    
    def test_update_activity(self, client):
        """اختبار تحديث نشاط الزائر"""
        with app.app_context():
            session = VisitorSession(
                session_id='test_session_activity',
                ip_address='192.168.1.101',
                page_views=1
            )
            db.session.add(session)
            db.session.commit()
            
            old_activity = session.last_activity
            old_page_views = session.page_views
            
            session.update_activity()
            
            assert session.last_activity > old_activity
            assert session.page_views == old_page_views + 1
    
    def test_to_dict(self, client):
        """اختبار تحويل الجلسة إلى قاموس"""
        with app.app_context():
            session = VisitorSession(
                session_id='test_dict_session',
                ip_address='192.168.1.102'
            )
            db.session.add(session)
            db.session.commit()
            
            data = session.to_dict()
            
            assert isinstance(data, dict)
            assert 'id' in data
            assert 'session_id' in data
            assert 'ip_address' in data
            assert 'page_views' in data
            assert 'is_active' in data

class TestVisitorStats:
    """اختبارات نموذج إحصائيات الزوار"""
    
    def test_create_visitor_stats(self, client):
        """اختبار إنشاء إحصائيات زوار جديدة"""
        with app.app_context():
            today = datetime.utcnow().date()
            stats = VisitorStats(
                date=today,
                unique_visitors=100,
                total_page_views=250,
                displayed_count=1350
            )
            db.session.add(stats)
            db.session.commit()
            
            assert stats.id is not None
            assert stats.date == today
            assert stats.unique_visitors == 100
            assert stats.total_page_views == 250
            assert stats.displayed_count == 1350
    
    def test_to_dict(self, client):
        """اختبار تحويل الإحصائيات إلى قاموس"""
        with app.app_context():
            today = datetime.utcnow().date()
            stats = VisitorStats(
                date=today,
                unique_visitors=50,
                total_page_views=120
            )
            db.session.add(stats)
            db.session.commit()
            
            data = stats.to_dict()
            
            assert isinstance(data, dict)
            assert 'id' in data
            assert 'date' in data
            assert 'unique_visitors' in data
            assert 'total_page_views' in data
            assert 'displayed_count' in data
