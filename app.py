import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")  


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback_secret_key_for_development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///pos_system.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول لهذه الصفحة'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import Employee
    return Employee.query.get(int(user_id))

# Import routes after app initialization
from routes import *

with app.app_context():
    # Import models to create tables
    import models
    db.create_all()
    
    # Create default admin user if doesn't exist
    from models import Employee
    from werkzeug.security import generate_password_hash
    
    if not Employee.query.filter_by(username='admin').first():
        admin = Employee(
            username='admin',
            email='admin@pos.com',
            full_name='المدير العام',
            role='admin',
            password_hash=generate_password_hash('Markode123@@@')
        )
        db.session.add(admin)
        db.session.commit()
        print("تم إنشاء حساب المدير الافتراضي:")
