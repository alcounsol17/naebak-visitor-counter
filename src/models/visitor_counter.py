from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random

db = SQLAlchemy()

class VisitorCounterSettings(db.Model):
    """إعدادات عداد الزوار التي يتحكم فيها الأدمن"""
    __tablename__ = 'visitor_counter_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    min_base_count = db.Column(db.Integer, default=1000, nullable=False)  # الحد الأدنى للرقم العشوائي
    max_base_count = db.Column(db.Integer, default=1500, nullable=False)  # الحد الأقصى للرقم العشوائي
    current_base_count = db.Column(db.Integer, default=1450, nullable=False)  # الرقم العشوائي الحالي
    last_update = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # آخر تحديث للرقم العشوائي
    update_interval = db.Column(db.Integer, default=30, nullable=False)  # فترة التحديث بالثواني
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # تفعيل/إلغاء تفعيل العداد
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<VisitorCounterSettings {self.min_base_count}-{self.max_base_count}>'
    
    def update_base_count(self):
        """تحديث الرقم العشوائي الأساسي"""
        self.current_base_count = random.randint(self.min_base_count, self.max_base_count)
        self.last_update = datetime.utcnow()
        db.session.commit()
        return self.current_base_count
    
    def should_update(self):
        """فحص ما إذا كان يجب تحديث الرقم العشوائي"""
        if not self.last_update:
            return True
        
        time_diff = (datetime.utcnow() - self.last_update).total_seconds()
        return time_diff >= self.update_interval
    
    def to_dict(self):
        return {
            'id': self.id,
            'min_base_count': self.min_base_count,
            'max_base_count': self.max_base_count,
            'current_base_count': self.current_base_count,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'update_interval': self.update_interval,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class VisitorSession(db.Model):
    """جلسات الزوار لحساب العدد الحقيقي"""
    __tablename__ = 'visitor_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False)  # معرف الجلسة الفريد
    ip_address = db.Column(db.String(45), nullable=True)  # عنوان IP
    user_agent = db.Column(db.Text, nullable=True)  # معلومات المتصفح
    first_visit = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # أول زيارة
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # آخر نشاط
    page_views = db.Column(db.Integer, default=1, nullable=False)  # عدد الصفحات المشاهدة
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # الجلسة نشطة
    
    def __repr__(self):
        return f'<VisitorSession {self.session_id}>'
    
    def update_activity(self):
        """تحديث آخر نشاط وزيادة عدد المشاهدات"""
        self.last_activity = datetime.utcnow()
        self.page_views += 1
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'first_visit': self.first_visit.isoformat() if self.first_visit else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'page_views': self.page_views,
            'is_active': self.is_active
        }

class VisitorStats(db.Model):
    """إحصائيات الزوار اليومية"""
    __tablename__ = 'visitor_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow().date, nullable=False, unique=True)
    unique_visitors = db.Column(db.Integer, default=0, nullable=False)  # الزوار الفريدون
    total_page_views = db.Column(db.Integer, default=0, nullable=False)  # إجمالي المشاهدات
    displayed_count = db.Column(db.Integer, default=0, nullable=False)  # العدد المعروض (مع الرقم العشوائي)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<VisitorStats {self.date}: {self.unique_visitors} visitors>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'unique_visitors': self.unique_visitors,
            'total_page_views': self.total_page_views,
            'displayed_count': self.displayed_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
