import pytest
import time
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from src.models.visitor_counter import VisitorSession, db
from src.main import app

class TestPerformance:
    """اختبارات الأداء والحمولة"""
    
    def test_api_response_time(self, client):
        """اختبار زمن استجابة API"""
        endpoints = [
            '/api/visitor-counter/count',
            '/api/visitor-counter/statistics',
            '/api/visitor-counter/admin/settings',
            '/health'
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 1.0  # يجب أن تكون الاستجابة أقل من ثانية واحدة
    
    def test_concurrent_visitor_tracking(self, client):
        """اختبار تتبع الزوار المتزامن"""
        def track_visitor(session_id):
            """دالة لتتبع زائر واحد"""
            with client.session_transaction() as sess:
                sess['visitor_session_id'] = f'concurrent_test_{session_id}'
            
            response = client.post('/api/visitor-counter/track')
            return response.status_code == 200
        
        # تشغيل 50 طلب متزامن
        num_requests = 50
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(track_visitor, i) for i in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        # يجب أن تنجح جميع الطلبات
        success_count = sum(results)
        assert success_count >= num_requests * 0.9  # 90% نجاح على الأقل
    
    def test_concurrent_count_requests(self, client):
        """اختبار طلبات العدد المتزامنة"""
        def get_count():
            """دالة للحصول على العدد"""
            response = client.get('/api/visitor-counter/count')
            if response.status_code == 200:
                data = json.loads(response.data)
                return data.get('count', 0)
            return None
        
        # تشغيل 100 طلب متزامن
        num_requests = 100
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(get_count) for _ in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        # يجب أن تنجح جميع الطلبات وتعيد قيماً صحيحة
        valid_results = [r for r in results if r is not None and r >= 0]
        assert len(valid_results) >= num_requests * 0.95  # 95% نجاح على الأقل
    
    def test_database_performance_large_dataset(self, client):
        """اختبار أداء قاعدة البيانات مع مجموعة بيانات كبيرة"""
        with app.app_context():
            # إنشاء 1000 جلسة زائر للاختبار
            sessions = []
            for i in range(1000):
                session = VisitorSession(
                    session_id=f'perf_test_session_{i}',
                    ip_address=f'192.168.{i//255}.{i%255}',
                    user_agent=f'Test Browser {i}',
                    first_visit=datetime.utcnow() - timedelta(minutes=i%60),
                    last_activity=datetime.utcnow() - timedelta(minutes=i%30),
                    page_views=(i % 10) + 1,
                    is_active=i % 2 == 0  # نصف الجلسات نشطة
                )
                sessions.append(session)
            
            # قياس وقت إدراج البيانات
            start_time = time.time()
            db.session.add_all(sessions)
            db.session.commit()
            insert_time = time.time() - start_time
            
            # يجب أن يكون الإدراج سريعاً (أقل من 5 ثوان)
            assert insert_time < 5.0
            
            # قياس وقت الاستعلام
            start_time = time.time()
            active_count = VisitorSession.query.filter_by(is_active=True).count()
            query_time = time.time() - start_time
            
            # يجب أن يكون الاستعلام سريعاً (أقل من ثانية واحدة)
            assert query_time < 1.0
            assert active_count > 0
    
    def test_memory_usage_stability(self, client):
        """اختبار استقرار استخدام الذاكرة"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # تشغيل 500 طلب متتالي
        for i in range(500):
            response = client.get('/api/visitor-counter/count')
            assert response.status_code == 200
            
            # فحص الذاكرة كل 100 طلب
            if i % 100 == 0:
                current_memory = process.memory_info().rss
                memory_increase = current_memory - initial_memory
                
                # يجب ألا تزيد الذاكرة بأكثر من 50 ميجابايت
                assert memory_increase < 50 * 1024 * 1024
    
    def test_settings_update_performance(self, client):
        """اختبار أداء تحديث الإعدادات"""
        settings_variations = [
            {'min_base_count': 1000, 'max_base_count': 2000, 'update_interval': 30},
            {'min_base_count': 2000, 'max_base_count': 3000, 'update_interval': 45},
            {'min_base_count': 3000, 'max_base_count': 4000, 'update_interval': 60},
            {'min_base_count': 500, 'max_base_count': 1500, 'update_interval': 20},
        ]
        
        total_time = 0
        for settings in settings_variations:
            start_time = time.time()
            response = client.put(
                '/api/visitor-counter/admin/settings',
                data=json.dumps(settings),
                content_type='application/json'
            )
            end_time = time.time()
            
            assert response.status_code == 200
            update_time = end_time - start_time
            total_time += update_time
            
            # كل تحديث يجب أن يكون أقل من ثانية واحدة
            assert update_time < 1.0
        
        # إجمالي وقت التحديثات يجب أن يكون معقولاً
        assert total_time < 3.0

class TestStressTest:
    """اختبارات الضغط والحمولة العالية"""
    
    def test_high_load_visitor_tracking(self, client):
        """اختبار تتبع الزوار تحت حمولة عالية"""
        def track_multiple_visitors(start_id, count):
            """تتبع عدة زوار"""
            success_count = 0
            for i in range(count):
                try:
                    with client.session_transaction() as sess:
                        sess['visitor_session_id'] = f'stress_test_{start_id}_{i}'
                    
                    response = client.post('/api/visitor-counter/track')
                    if response.status_code == 200:
                        success_count += 1
                except Exception:
                    pass  # تجاهل الأخطاء في اختبار الضغط
            
            return success_count
        
        # تشغيل 20 thread كل منها يتتبع 50 زائر (1000 زائر إجمالي)
        num_threads = 20
        visitors_per_thread = 50
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(track_multiple_visitors, i, visitors_per_thread)
                for i in range(num_threads)
            ]
            results = [future.result() for future in as_completed(futures)]
        
        total_success = sum(results)
        total_expected = num_threads * visitors_per_thread
        
        # يجب أن ينجح 80% من الطلبات على الأقل تحت الضغط العالي
        success_rate = total_success / total_expected
        assert success_rate >= 0.8
    
    def test_rapid_settings_changes(self, client):
        """اختبار تغيير الإعدادات بسرعة"""
        def change_settings(iteration):
            """تغيير الإعدادات"""
            settings = {
                'min_base_count': 1000 + (iteration * 100),
                'max_base_count': 2000 + (iteration * 100),
                'update_interval': 30 + (iteration % 10)
            }
            
            try:
                response = client.put(
                    '/api/visitor-counter/admin/settings',
                    data=json.dumps(settings),
                    content_type='application/json'
                )
                return response.status_code == 200
            except Exception:
                return False
        
        # تشغيل 100 تغيير سريع للإعدادات
        num_changes = 100
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(change_settings, i) for i in range(num_changes)]
            results = [future.result() for future in as_completed(futures)]
        
        success_count = sum(results)
        success_rate = success_count / num_changes
        
        # يجب أن ينجح 70% من التغييرات على الأقل
        assert success_rate >= 0.7

class TestScalability:
    """اختبارات قابلية التوسع"""
    
    def test_large_session_cleanup(self, client):
        """اختبار تنظيف عدد كبير من الجلسات"""
        with app.app_context():
            # إنشاء 5000 جلسة قديمة
            old_sessions = []
            for i in range(5000):
                session = VisitorSession(
                    session_id=f'cleanup_test_{i}',
                    ip_address=f'10.0.{i//255}.{i%255}',
                    first_visit=datetime.utcnow() - timedelta(hours=25 + i%24),
                    last_activity=datetime.utcnow() - timedelta(hours=25 + i%24),
                    is_active=True
                )
                old_sessions.append(session)
            
            db.session.add_all(old_sessions)
            db.session.commit()
        
        # قياس وقت التنظيف
        start_time = time.time()
        response = client.post('/api/visitor-counter/admin/cleanup')
        cleanup_time = time.time() - start_time
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # يجب أن يكون التنظيف سريعاً حتى مع عدد كبير من الجلسات
        assert cleanup_time < 10.0  # أقل من 10 ثوان
        assert data['cleaned_sessions'] > 0
    
    def test_statistics_calculation_performance(self, client):
        """اختبار أداء حساب الإحصائيات مع بيانات كثيرة"""
        with app.app_context():
            # إنشاء بيانات كثيرة للاختبار
            sessions = []
            for i in range(2000):
                session = VisitorSession(
                    session_id=f'stats_test_{i}',
                    ip_address=f'172.16.{i//255}.{i%255}',
                    first_visit=datetime.utcnow() - timedelta(hours=i%24),
                    last_activity=datetime.utcnow() - timedelta(minutes=i%60),
                    page_views=(i % 20) + 1,
                    is_active=i % 3 == 0  # ثلث الجلسات نشطة
                )
                sessions.append(session)
            
            db.session.add_all(sessions)
            db.session.commit()
        
        # قياس وقت حساب الإحصائيات
        start_time = time.time()
        response = client.get('/api/visitor-counter/statistics')
        stats_time = time.time() - start_time
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # يجب أن يكون حساب الإحصائيات سريعاً
        assert stats_time < 3.0  # أقل من 3 ثوان
        assert 'data' in data
        assert data['data']['active_visitors'] > 0
