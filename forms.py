from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, DecimalField, IntegerField, SelectField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Email, NumberRange, Optional, Length
from wtforms import StringField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(message='اسم المستخدم مطلوب')])
    password = PasswordField('كلمة المرور', validators=[DataRequired(message='كلمة المرور مطلوبة')])
    remember_me = BooleanField('تذكرني')

class ProductForm(FlaskForm):
    name = StringField('اسم المنتج (إنجليزي)', validators=[DataRequired(message='اسم المنتج مطلوب')])
    name_ar = StringField('اسم المنتج (عربي)', validators=[DataRequired(message='اسم المنتج بالعربية مطلوب')])
    description = TextAreaField('وصف المنتج')
    barcode = StringField('الباركود')
    sku = StringField('رمز المنتج (SKU)', validators=[DataRequired(message='رمز المنتج مطلوب')])
    price = DecimalField('سعر البيع', validators=[DataRequired(message='سعر البيع مطلوب'), NumberRange(min=0.01, message='السعر يجب أن يكون أكبر من صفر')])
    cost_price = DecimalField('سعر التكلفة', validators=[Optional(), NumberRange(min=0, message='سعر التكلفة يجب أن يكون أكبر من أو يساوي صفر')])
    quantity = IntegerField('الكمية', validators=[DataRequired(message='الكمية مطلوبة'), NumberRange(min=0, message='الكمية يجب أن تكون أكبر من أو تساوي صفر')])
    min_quantity = IntegerField('الحد الأدنى للكمية', validators=[DataRequired(message='الحد الأدنى للكمية مطلوب'), NumberRange(min=0, message='الحد الأدنى يجب أن يكون أكبر من أو يساوي صفر')])
    category_name = StringField('الفئة', validators=[DataRequired(message='الفئة مطلوبة')])
    image = FileField('صورة المنتج', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'يجب أن تكون الصورة من نوع JPG أو PNG')])

class EmployeeForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(message='اسم المستخدم مطلوب'), Length(min=3, max=64, message='اسم المستخدم يجب أن يكون بين 3 و 64 حرف')])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(message='البريد الإلكتروني مطلوب'), Email(message='البريد الإلكتروني غير صحيح')])
    full_name = StringField('الاسم الكامل', validators=[DataRequired(message='الاسم الكامل مطلوب')])
    password = PasswordField('كلمة المرور', validators=[DataRequired(message='كلمة المرور مطلوبة'), Length(min=6, message='كلمة المرور يجب أن تكون على الأقل 6 أحرف')])
    role = SelectField('الدور', choices=[('cashier', 'كاشير'), ('manager', 'مدير'), ('admin', 'مدير عام')], validators=[DataRequired(message='الدور مطلوب')])
    is_active = BooleanField('مفعل', default=True)
