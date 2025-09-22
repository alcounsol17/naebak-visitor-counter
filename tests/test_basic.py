import pytest
import json
from src.main import app

class TestBasicFunctionality:
    """اختبارات الوظائف الأساسية"""
    
    def test_app_creation(self):
        """اختبار إنشاء التطبيق"""
        assert app is not None
        assert app.name == 'src.main'
    
    def test_health_endpoint(self, client):
        """اختبار نقطة فحص الصحة"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['service'] == 'naebak-visitor-counter'
        assert data['status'] == 'healthy'
    
    def test_visitor_count_endpoint(self, client):
        """اختبار نقطة الحصول على عدد الزوار"""
        response = client.get('/api/visitor-counter/count')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'count' in data
        assert isinstance(data['count'], int)
        assert data['count'] >= 0
    
    def test_track_visitor_endpoint(self, client):
        """اختبار نقطة تتبع الزوار"""
        response = client.post('/api/visitor-counter/track')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
    
    def test_statistics_endpoint(self, client):
        """اختبار نقطة الإحصائيات"""
        response = client.get('/api/visitor-counter/statistics')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data
    
    def test_admin_settings_get(self, client):
        """اختبار الحصول على إعدادات الأدمن"""
        response = client.get('/api/visitor-counter/admin/settings')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data
    
    def test_admin_settings_update_valid(self, client):
        """اختبار تحديث إعدادات الأدمن بقيم صحيحة"""
        valid_settings = {
            'min_base_count': 2000,
            'max_base_count': 3000,
            'update_interval': 45
        }
        
        response = client.put(
            '/api/visitor-counter/admin/settings',
            data=json.dumps(valid_settings),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
    
    def test_admin_settings_update_invalid(self, client):
        """اختبار تحديث إعدادات الأدمن بقيم غير صحيحة"""
        invalid_settings = {
            'min_base_count': 3000,
            'max_base_count': 2000,  # أقل من الحد الأدنى
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
    
    def test_toggle_counter(self, client):
        """اختبار تغيير حالة العداد"""
        # تفعيل العداد
        toggle_data = {'is_active': True}
        response = client.post(
            '/api/visitor-counter/admin/toggle',
            data=json.dumps(toggle_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
        # إلغاء تفعيل العداد
        toggle_data = {'is_active': False}
        response = client.post(
            '/api/visitor-counter/admin/toggle',
            data=json.dumps(toggle_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
    
    def test_cleanup_sessions(self, client):
        """اختبار تنظيف الجلسات"""
        response = client.post('/api/visitor-counter/admin/cleanup')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'cleaned_sessions' in data
