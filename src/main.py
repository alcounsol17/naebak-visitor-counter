import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.visitor_counter import db
from src.routes.visitor_counter import visitor_counter_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'naebak_visitor_counter_secret_key_2024'

# تفعيل CORS للسماح بالطلبات من الواجهة الأمامية
CORS(app, supports_credentials=True)

# تسجيل مسارات API
app.register_blueprint(visitor_counter_bp, url_prefix='/api/visitor-counter')

# إعداد قاعدة البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'visitor_counter.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# إنشاء الجداول
with app.app_context():
    db.create_all()
    
    # إنشاء الإعدادات الافتراضية إذا لم تكن موجودة
    from src.services.visitor_service import VisitorCounterService
    VisitorCounterService.get_or_create_settings()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "Naebak Visitor Counter Service - API is running", 200

# مسار صحة الخدمة
@app.route('/health')
def health():
    return {
        'service': 'naebak-visitor-counter',
        'status': 'healthy',
        'message': 'خدمة عداد الزوار تعمل بشكل طبيعي'
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
