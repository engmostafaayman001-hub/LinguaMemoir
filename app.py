import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash
from flask_migrate import Migrate

# ==========================
# 1️⃣ إنشاء كائن Flask أولاً
# ==========================
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback_secret_key_for_development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# ========================
# 2️⃣ إعدادات قاعدة البيانات
# ========================
class Base(DeclarativeBase):
    pass

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///pos_system.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# ==========================
# 3️⃣ تهيئة SQLAlchemy و Migrate و LoginManager
# ==========================
db = SQLAlchemy(app, model_class=Base)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول لهذه الصفحة'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import Employee
    return Employee.query.get(int(user_id))

# ==========================
# 4️⃣ استيراد المسارات بعد تهيئة app
# ==========================
from routes import *

# ==========================
# 5️⃣ إنشاء الجداول وحساب المدير الافتراضي أو تعديل بياناته
# ==========================
with app.app_context():
    import models
    db.create_all()

    from models import Employee
    admin = Employee.query.filter_by(username='admin').first()
    
    if not admin:
        # إنشاء المدير إذا لم يكن موجودًا
        admin = Employee(
            username='admin',
            email='admin@pos.com',
            full_name='المدير العام',
            role='admin',
            is_active=True,
            password_hash=generate_password_hash('Markode123@@@')
        )
        db.session.add(admin)
        db.session.commit()
        print("تم إنشاء حساب المدير الافتراضي")
    else:
        # السماح بتعديل بيانات المدير الموجود بالفعل إذا رغبت
        admin.email = 'admin@pos.com'
        admin.full_name = 'المدير العام'
        admin.role = 'admin'
        admin.is_active = True
        db.session.commit()
        print("تم تحديث بيانات المدير الافتراضي إذا كانت تحتاج تعديل")
