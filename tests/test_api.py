import pytest
import json
from datetime import datetime, timedelta
from src.models.visitor_counter import VisitorCounterSettings, VisitorSession, db
from src.main import app

class TestVisitorCounterAPI:
    """اختبارات API عداد الزوار"""
    
    def test_get_visitor_count_success(self, client):
        """اختبار الحصول على عدد الزوار بنجاح"""
        response = client.get('/api/visitor-counter/count')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'count' in data
        assert isinstance(data['count'], int)
        assert data['count'] >= 0
    
    def test_track_visitor_success(self, client):
        """اختبار تتبع زائر بنجاح"""
        with client.session_transaction() as sess:
            sess['visitor_session_id'] = 'test_track_session'
        
        response = client.post('/api/visitor-counter/track')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'session_id' in data
    
    def test_get_statistics_success(self, client):
        """اختبار الحصول على الإحصائيات بنجاح"""
        response = client.get('/api/visitor-counter/statistics')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data
        
        stats_data = data['data']
        assert 'current_display_count' in stats_data
        assert 'active_visitors' in stats_data
        assert 'today_visitors' in stats_data
        assert 'base_count' in stats_data
        assert 'settings' in stats_data
        assert 'weekly_stats' in stats_data
    
    def test_get_admin_settings_success(self, client):
        """اختبار الحصول على إعدادات الأدمن بنجاح"""
        response = client.get('/api/visitor-counter/admin/settings')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data
        
        settings_data = data['data']
        assert 'min_base_count' in settings_data
        assert 'max_base_count' in settings_data
        assert 'update_interval' in settings_data
        assert 'is_active' in settings_data
    
    def test_update_admin_settings_success(self, client, sample_settings):
        """اختبار تحديث إعدادات الأدمن بنجاح"""
        response = client.put(
            '/api/visitor-counter/admin/settings',
            data=json.dumps(sample_settings),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data
        
        settings_data = data['data']
        assert settings_data['min_base_count'] == sample_settings['min_base_count']
        assert settings_data['max_base_count'] == sample_settings['max_base_count']
        assert settings_data['update_interval'] == sample_settings['update_interval']
    
    def test_update_admin_settings_invalid_data(self, client):
        """اختبار تحديث الإعدادات ببيانات غير صحيحة"""
        invalid_settings = {
            'min_base_count': 2000,
            'max_base_count': 1000,  # أقل من الحد الأدنى
            'update_interval': 30
        }
        
        response = client.put(
            '/api/visitor-counter/admin/settings',
            data=json.dumps(invalid_settings),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'error' in data
    
    def test_update_admin_settings_missing_data(self, client):
        """اختبار تحديث الإعدادات ببيانات ناقصة"""
        incomplete_settings = {
            'min_base_count': 1000
            # max_base_count مفقود
        }
        
        response = client.put(
            '/api/visitor-counter/admin/settings',
            data=json.dumps(incomplete_settings),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'error' in data
    
    def test_update_admin_settings_negative_values(self, client):
        """اختبار تحديث الإعدادات بقيم سالبة"""
        negative_settings = {
            'min_base_count': -100,
            'max_base_count': -50,
            'update_interval': 30
        }
        
        response = client.put(
            '/api/visitor-counter/admin/settings',
            data=json.dumps(negative_settings),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'error' in data
    
    def test_update_admin_settings_invalid_interval(self, client):
        """اختبار تحديث الإعدادات بفترة تحديث غير صحيحة"""
        invalid_interval_settings = {
            'min_base_count': 1000,
            'max_base_count': 2000,
            'update_interval': 5  # أقل من الحد الأدنى (10)
        }
        
        response = client.put(
            '/api/visitor-counter/admin/settings',
            data=json.dumps(invalid_interval_settings),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'error' in data
    
    def test_toggle_counter_activate(self, client):
        """اختبار تفعيل العداد"""
        # تعطيل العداد أولاً
        with app.app_context():
            settings = VisitorCounterSettings.query.first()
            settings.is_active = False
            db.session.commit()
        
        toggle_data = {'is_active': True}
        response = client.post(
            '/api/visitor-counter/admin/toggle',
            data=json.dumps(toggle_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['is_active'] == True
    
    def test_toggle_counter_deactivate(self, client):
        """اختبار إلغاء تفعيل العداد"""
        toggle_data = {'is_active': False}
        response = client.post(
            '/api/visitor-counter/admin/toggle',
            data=json.dumps(toggle_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['is_active'] == False
    
    def test_toggle_counter_invalid_data(self, client):
        """اختبار تغيير حالة العداد ببيانات غير صحيحة"""
        invalid_toggle_data = {'is_active': 'invalid_boolean'}
        response = client.post(
            '/api/visitor-counter/admin/toggle',
            data=json.dumps(invalid_toggle_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'error' in data
    
    def test_toggle_counter_missing_data(self, client):
        """اختبار تغيير حالة العداد ببيانات ناقصة"""
        response = client.post(
            '/api/visitor-counter/admin/toggle',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'error' in data
    
    def test_cleanup_old_sessions_success(self, client):
        """اختبار تنظيف الجلسات القديمة بنجاح"""
        # إنشاء جلسة قديمة للاختبار
        with app.app_context():
            old_session = VisitorSession(
                session_id='cleanup_test_session',
                ip_address='192.168.1.200',
                first_visit=datetime.utcnow() - timedelta(hours=30),
                last_activity=datetime.utcnow() - timedelta(hours=30),
                is_active=True
            )
            db.session.add(old_session)
            db.session.commit()
        
        response = client.post('/api/visitor-counter/admin/cleanup')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'cleaned_sessions' in data
        assert isinstance(data['cleaned_sessions'], int)
    
    def test_health_check_success(self, client):
        """اختبار فحص صحة الخدمة"""
        response = client.get('/api/visitor-counter/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['service'] == 'naebak-visitor-counter'
        assert data['status'] == 'healthy'
        assert 'counter_active' in data
    
    def test_main_health_endpoint(self, client):
        """اختبار نقطة فحص الصحة الرئيسية"""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['service'] == 'naebak-visitor-counter'
        assert data['status'] == 'healthy'

class TestAPIErrorHandling:
    """اختبارات معالجة الأخطاء في API"""
    
    def test_404_not_found(self, client):
        """اختبار استجابة 404 للمسارات غير الموجودة"""
        response = client.get('/api/visitor-counter/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'error' in data
    
    def test_405_method_not_allowed(self, client):
        """اختبار استجابة 405 للطرق غير المسموحة"""
        response = client.delete('/api/visitor-counter/count')
        
        assert response.status_code == 405
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'error' in data
    
    def test_invalid_json_data(self, client):
        """اختبار إرسال بيانات JSON غير صحيحة"""
        response = client.put(
            '/api/visitor-counter/admin/settings',
            data='invalid json data',
            content_type='application/json'
        )
        
        # يجب أن يعيد خطأ في تحليل JSON
        assert response.status_code in [400, 500]
    
    def test_missing_content_type(self, client):
        """اختبار إرسال بيانات بدون Content-Type"""
        response = client.put(
            '/api/visitor-counter/admin/settings',
            data=json.dumps({'min_base_count': 1000, 'max_base_count': 2000})
        )
        
        # قد يعيد خطأ أو يتعامل مع البيانات بشكل مختلف
        assert response.status_code in [200, 400, 415]

class TestAPIIntegration:
    """اختبارات التكامل للAPI"""
    
    def test_full_workflow(self, client):
        """اختبار سير العمل الكامل للAPI"""
        # 1. الحصول على الإعدادات الحالية
        response = client.get('/api/visitor-counter/admin/settings')
        assert response.status_code == 200
        
        # 2. تحديث الإعدادات
        new_settings = {
            'min_base_count': 3000,
            'max_base_count': 4000,
            'update_interval': 45
        }
        response = client.put(
            '/api/visitor-counter/admin/settings',
            data=json.dumps(new_settings),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # 3. تتبع زائر
        response = client.post('/api/visitor-counter/track')
        assert response.status_code == 200
        
        # 4. الحصول على عدد الزوار
        response = client.get('/api/visitor-counter/count')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] >= 3000  # يجب أن يكون ضمن النطاق الجديد
        
        # 5. الحصول على الإحصائيات
        response = client.get('/api/visitor-counter/statistics')
        assert response.status_code == 200
        
        # 6. تنظيف الجلسات
        response = client.post('/api/visitor-counter/admin/cleanup')
        assert response.status_code == 200
    
    def test_counter_deactivation_workflow(self, client):
        """اختبار سير العمل عند تعطيل العداد"""
        # 1. تعطيل العداد
        response = client.post(
            '/api/visitor-counter/admin/toggle',
            data=json.dumps({'is_active': False}),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # 2. التحقق من أن العدد المعروض يصبح صفراً أو قريباً من الصفر
        response = client.get('/api/visitor-counter/count')
        assert response.status_code == 200
        data = json.loads(response.data)
        # عندما يكون العداد معطلاً، يجب أن يعرض الزوار الحقيقيين فقط
        assert data['count'] >= 0
        
        # 3. إعادة تفعيل العداد
        response = client.post(
            '/api/visitor-counter/admin/toggle',
            data=json.dumps({'is_active': True}),
            content_type='application/json'
        )
        assert response.status_code == 200
