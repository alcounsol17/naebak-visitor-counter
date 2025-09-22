import pytest
import os
import sys
import tempfile
from datetime import datetime, timedelta

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.main import app
from src.models.visitor_counter import db, VisitorCounterSettings, VisitorSession, VisitorStats

@pytest.fixture
def client():
    """إنشاء عميل اختبار Flask"""
    # إنشاء قاعدة بيانات مؤقتة للاختبار
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # إنشاء إعدادات افتراضية للاختبار
            settings = VisitorCounterSettings(
                min_base_count=1000,
                max_base_count=1500,
                current_base_count=1250,
                update_interval=30,
                is_active=True
            )
            db.session.add(settings)
            db.session.commit()
            
        yield client
    
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

@pytest.fixture
def sample_settings():
    """إعدادات عينة للاختبار"""
    return {
        'min_base_count': 2000,
        'max_base_count': 3000,
        'update_interval': 60
    }

@pytest.fixture
def sample_visitor_sessions():
    """جلسات زوار عينة للاختبار"""
    return [
        {
            'session_id': 'test_session_1',
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0 Test Browser',
            'first_visit': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'page_views': 1,
            'is_active': True
        },
        {
            'session_id': 'test_session_2',
            'ip_address': '192.168.1.2',
            'user_agent': 'Chrome Test Browser',
            'first_visit': datetime.utcnow() - timedelta(minutes=10),
            'last_activity': datetime.utcnow() - timedelta(minutes=5),
            'page_views': 3,
            'is_active': True
        },
        {
            'session_id': 'test_session_old',
            'ip_address': '192.168.1.3',
            'user_agent': 'Old Browser',
            'first_visit': datetime.utcnow() - timedelta(hours=25),
            'last_activity': datetime.utcnow() - timedelta(hours=25),
            'page_views': 1,
            'is_active': True
        }
    ]

@pytest.fixture
def create_test_sessions(client, sample_visitor_sessions):
    """إنشاء جلسات اختبار في قاعدة البيانات"""
    with app.app_context():
        for session_data in sample_visitor_sessions:
            session = VisitorSession(**session_data)
            db.session.add(session)
        db.session.commit()
        
        return len(sample_visitor_sessions)
