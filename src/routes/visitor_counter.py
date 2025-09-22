from flask import Blueprint, request, jsonify, session
from src.models.visitor_counter import db
from src.services.visitor_service import VisitorCounterService
import logging

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

visitor_counter_bp = Blueprint('visitor_counter', __name__)

@visitor_counter_bp.route('/count', methods=['GET'])
def get_visitor_count():
    """الحصول على عدد الزوار المعروض"""
    try:
        # تتبع الزائر الحالي
        VisitorCounterService.track_visitor()
        
        # الحصول على العدد المعروض
        displayed_count = VisitorCounterService.get_displayed_visitor_count()
        
        return jsonify({
            'success': True,
            'count': displayed_count,
            'message': 'تم الحصول على عدد الزوار بنجاح'
        }), 200
        
    except Exception as e:
        logger.error(f"خطأ في الحصول على عدد الزوار: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'حدث خطأ في الحصول على عدد الزوار',
            'details': str(e)
        }), 500

@visitor_counter_bp.route('/track', methods=['POST'])
def track_visitor():
    """تتبع زائر جديد"""
    try:
        visitor_session = VisitorCounterService.track_visitor()
        
        return jsonify({
            'success': True,
            'session_id': visitor_session.session_id,
            'message': 'تم تتبع الزائر بنجاح'
        }), 200
        
    except Exception as e:
        logger.error(f"خطأ في تتبع الزائر: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'حدث خطأ في تتبع الزائر',
            'details': str(e)
        }), 500

@visitor_counter_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """الحصول على إحصائيات شاملة للزوار"""
    try:
        stats = VisitorCounterService.get_visitor_statistics()
        
        return jsonify({
            'success': True,
            'data': stats,
            'message': 'تم الحصول على الإحصائيات بنجاح'
        }), 200
        
    except Exception as e:
        logger.error(f"خطأ في الحصول على الإحصائيات: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'حدث خطأ في الحصول على الإحصائيات',
            'details': str(e)
        }), 500

@visitor_counter_bp.route('/admin/settings', methods=['GET'])
def get_admin_settings():
    """الحصول على إعدادات العداد للأدمن"""
    try:
        settings = VisitorCounterService.get_or_create_settings()
        
        return jsonify({
            'success': True,
            'data': settings.to_dict(),
            'message': 'تم الحصول على الإعدادات بنجاح'
        }), 200
        
    except Exception as e:
        logger.error(f"خطأ في الحصول على الإعدادات: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'حدث خطأ في الحصول على الإعدادات',
            'details': str(e)
        }), 500

@visitor_counter_bp.route('/admin/settings', methods=['PUT'])
def update_admin_settings():
    """تحديث إعدادات العداد من قبل الأدمن"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'لم يتم إرسال بيانات'
            }), 400
        
        min_count = data.get('min_base_count')
        max_count = data.get('max_base_count')
        interval = data.get('update_interval', 30)
        
        # التحقق من صحة البيانات
        if min_count is None or max_count is None:
            return jsonify({
                'success': False,
                'error': 'يجب إرسال الحد الأدنى والأقصى للعداد'
            }), 400
        
        if min_count >= max_count:
            return jsonify({
                'success': False,
                'error': 'الحد الأدنى يجب أن يكون أقل من الحد الأقصى'
            }), 400
        
        if min_count < 0 or max_count < 0:
            return jsonify({
                'success': False,
                'error': 'القيم يجب أن تكون أرقام موجبة'
            }), 400
        
        if interval < 10 or interval > 300:
            return jsonify({
                'success': False,
                'error': 'فترة التحديث يجب أن تكون بين 10 و 300 ثانية'
            }), 400
        
        # تحديث الإعدادات
        settings = VisitorCounterService.update_settings(min_count, max_count, interval)
        
        return jsonify({
            'success': True,
            'data': settings.to_dict(),
            'message': 'تم تحديث الإعدادات بنجاح'
        }), 200
        
    except Exception as e:
        logger.error(f"خطأ في تحديث الإعدادات: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'حدث خطأ في تحديث الإعدادات',
            'details': str(e)
        }), 500

@visitor_counter_bp.route('/admin/toggle', methods=['POST'])
def toggle_counter():
    """تفعيل أو إلغاء تفعيل العداد"""
    try:
        data = request.get_json()
        
        if not data or 'is_active' not in data:
            return jsonify({
                'success': False,
                'error': 'يجب إرسال حالة التفعيل'
            }), 400
        
        is_active = data.get('is_active')
        
        if not isinstance(is_active, bool):
            return jsonify({
                'success': False,
                'error': 'حالة التفعيل يجب أن تكون true أو false'
            }), 400
        
        settings = VisitorCounterService.toggle_counter_status(is_active)
        
        status_text = 'تم تفعيل' if is_active else 'تم إلغاء تفعيل'
        
        return jsonify({
            'success': True,
            'data': settings.to_dict(),
            'message': f'{status_text} العداد بنجاح'
        }), 200
        
    except Exception as e:
        logger.error(f"خطأ في تغيير حالة العداد: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'حدث خطأ في تغيير حالة العداد',
            'details': str(e)
        }), 500

@visitor_counter_bp.route('/admin/cleanup', methods=['POST'])
def cleanup_old_sessions():
    """تنظيف الجلسات القديمة"""
    try:
        cleaned_count = VisitorCounterService.cleanup_old_sessions()
        
        return jsonify({
            'success': True,
            'cleaned_sessions': cleaned_count,
            'message': f'تم تنظيف {cleaned_count} جلسة قديمة'
        }), 200
        
    except Exception as e:
        logger.error(f"خطأ في تنظيف الجلسات: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'حدث خطأ في تنظيف الجلسات',
            'details': str(e)
        }), 500

@visitor_counter_bp.route('/health', methods=['GET'])
def health_check():
    """فحص صحة الخدمة"""
    try:
        # فحص الاتصال بقاعدة البيانات
        settings = VisitorCounterService.get_or_create_settings()
        
        return jsonify({
            'success': True,
            'service': 'naebak-visitor-counter',
            'status': 'healthy',
            'counter_active': settings.is_active,
            'message': 'الخدمة تعمل بشكل طبيعي'
        }), 200
        
    except Exception as e:
        logger.error(f"خطأ في فحص صحة الخدمة: {str(e)}")
        return jsonify({
            'success': False,
            'service': 'naebak-visitor-counter',
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# معالج الأخطاء
@visitor_counter_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'المسار غير موجود',
        'message': 'تأكد من صحة رابط API'
    }), 404

@visitor_counter_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 'الطريقة غير مسموحة',
        'message': 'تأكد من استخدام الطريقة الصحيحة للطلب'
    }), 405

@visitor_counter_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'خطأ داخلي في الخادم',
        'message': 'حدث خطأ غير متوقع'
    }), 500
