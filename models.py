from app import db
from flask_login import UserMixin
from datetime import datetime

# ==========================
# نموذج الموظف
# ==========================
class Employee(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='cashier')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    sales = db.relationship('Sale', backref='employee', lazy=True)
    inventory_movements = db.relationship('InventoryMovement', backref='employee', lazy=True)

    def has_permission(self, permission):
        permissions = {
            'admin': ['manage_employees', 'manage_inventory', 'view_reports', 'make_sales', 'manage_products'],
            'manager': ['manage_inventory', 'view_reports', 'edit_products', 'make_sales', 'manage_products'],
            'cashier': ['make_sales']
        }
        return permission in permissions.get(self.role, [])


# ==========================
# نموذج الفئة
# ==========================
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_ar = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    products = db.relationship('Product', backref='category', lazy=True)


# ==========================
# نموذج المنتج
# ==========================
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    name_ar = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    barcode = db.Column(db.String(50), unique=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    cost_price = db.Column(db.Numeric(10, 2))
    quantity = db.Column(db.Integer, nullable=False, default=0)
    min_quantity = db.Column(db.Integer, default=5)
    image_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign Key
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    # العلاقات
    sale_items = db.relationship('SaleItem', backref='product', lazy=True)
    inventory_movements = db.relationship('InventoryMovement', backref='product', lazy=True)

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_quantity


# ==========================
# نموذج البيع
# ==========================
class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), unique=True, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    payment_method = db.Column(db.String(20), default='cash')
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Key
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)

    # العلاقات
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')


# ==========================
# عناصر البيع
# ==========================
class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)

    # نسخة من بيانات المنتج وقت البيع
    product_name = db.Column(db.String(200))
    product_sku = db.Column(db.String(50))

    # Foreign Keys
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)


# ==========================
# حركة المخزون
# ==========================
class InventoryMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # أنواع الحركة: in, out, adjustment, update, deleted
    movement_type = db.Column(db.String(20), nullable=False)
    
    quantity = db.Column(db.Integer, nullable=False)
    previous_quantity = db.Column(db.Integer, nullable=False)
    new_quantity = db.Column(db.Integer, nullable=False)
    
    reason = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Keys
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
