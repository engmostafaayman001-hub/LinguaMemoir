from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from app import app, db
from models import Employee, Product, Category, Sale, SaleItem, InventoryMovement
from forms import LoginForm, ProductForm, EmployeeForm
from utils import allowed_file, generate_invoice_number, create_invoice_pdf
import os
from datetime import datetime, timedelta
from sqlalchemy import func, or_

# =========================
# صفحات تسجيل الدخول والخروج
# =========================
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        employee = Employee.query.filter_by(username=form.username.data).first()
        if employee and check_password_hash(employee.password_hash, form.password.data):
            if employee.is_active:
                login_user(employee, remember=form.remember_me.data)
                flash(f'مرحباً {employee.full_name}', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('حسابك غير مفعل. يرجى التواصل مع المدير', 'error')
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('login'))

# =========================
# لوحة التحكم Dashboard
# =========================
@app.route('/dashboard')
@login_required
def dashboard():
    today = datetime.utcnow().date()
    today_sales = Sale.query.filter(func.date(Sale.created_at) == today).all()
    today_revenue = sum(sale.total_amount for sale in today_sales)
    today_transactions = len(today_sales)
    
    week_start = today - timedelta(days=today.weekday())
    week_sales = Sale.query.filter(Sale.created_at >= week_start).all()
    week_revenue = sum(sale.total_amount for sale in week_sales)
    
    low_stock_products = Product.query.filter(
        Product.quantity <= Product.min_quantity,
        Product.is_active == True
    ).all()
    
    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(10).all()
    
    total_products = Product.query.filter_by(is_active=True).count()
    
    return render_template('dashboard.html',
                         today_revenue=today_revenue,
                         today_transactions=today_transactions,
                         week_revenue=week_revenue,
                         low_stock_products=low_stock_products,
                         recent_sales=recent_sales,
                         total_products=total_products)

# =========================
# سجل الأنشطة / المخزون
# =========================
@app.route('/logs')
@login_required
def logs():
    if current_user.role not in ['admin', 'manager']:
        flash('ليس لديك صلاحية للوصول لسجل الأنشطة', 'error')
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str).strip()
    movement_type = request.args.get('movement_type', '', type=str).strip()
    
    query = InventoryMovement.query.join(Product, isouter=True).join(Employee, isouter=True)
    
    if search:
        query = query.filter(
            db.or_(
                Product.name_ar.ilike(f'%{search}%'),
                Product.name.ilike(f'%{search}%'),
                Employee.full_name.ilike(f'%{search}%')
            )
        )
    
    if movement_type:
        query = query.filter(InventoryMovement.movement_type == movement_type)
    
    logs_paginated = query.order_by(InventoryMovement.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template(
        'logs.html',
        logs=logs_paginated,
        search=search,
        selected_type=movement_type
    )

# =========================
# نقاط البيع POS
# =========================
@app.route('/pos')
@login_required
def pos():
    if not current_user.has_permission('make_sales'):
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    
    categories = Category.query.all()
    return render_template('pos.html', categories=categories)

@app.route('/api/search_products')
@login_required
def search_products():
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    products = Product.query.filter(
        Product.is_active == True,
        or_(
            Product.name_ar.contains(query),
            Product.name.contains(query),
            Product.barcode.contains(query),
            Product.sku.contains(query)
        )
    ).limit(20).all()
    
    return jsonify([{
        'id': product.id,
        'name': product.name_ar,
        'name_en': product.name,
        'barcode': product.barcode,
        'sku': product.sku,
        'price': float(product.price),
        'quantity': product.quantity,
        'image_url': product.image_url
    } for product in products])

@app.route('/api/get_product_by_barcode/<barcode>')
@login_required
def get_product_by_barcode(barcode):
    product = Product.query.filter_by(barcode=barcode, is_active=True).first()
    if product:
        return jsonify({
            'id': product.id,
            'name': product.name_ar,
            'name_en': product.name,
            'barcode': product.barcode,
            'sku': product.sku,
            'price': float(product.price),
            'quantity': product.quantity,
            'image_url': product.image_url
        })
    return jsonify({'error': 'المنتج غير موجود'}), 404

@app.route('/api/process_sale', methods=['POST'])
@login_required
def process_sale():
    if not current_user.has_permission('make_sales'):
        return jsonify({'error': 'ليس لديك صلاحية لإجراء المبيعات'}), 403
    
    data = request.json
    items = data.get('items', [])
    payment_method = data.get('payment_method', 'cash')
    customer_name = data.get('customer_name', '')
    customer_phone = data.get('customer_phone', '')
    discount_amount = float(data.get('discount_amount', 0))
    
    if not items:
        return jsonify({'error': 'لا يوجد منتجات في السلة'}), 400
    
    try:
        sale = Sale(
            invoice_number=generate_invoice_number(),
            total_amount=0,
            discount_amount=discount_amount,
            payment_method=payment_method,
            customer_name=customer_name,
            customer_phone=customer_phone,
            employee_id=current_user.id
        )
        
        total_amount = 0
        sale_items = []
        
        for item_data in items:
            product = Product.query.get(item_data['product_id'])
            if not product:
                return jsonify({'error': f'المنتج غير موجود: {item_data["product_id"]}'}), 400
            
            quantity = int(item_data['quantity'])
            if product.quantity < quantity:
                return jsonify({'error': f'الكمية المطلوبة غير متوفرة للمنتج: {product.name_ar}'}), 400
            
            unit_price = float(item_data['price'])
            item_total = unit_price * quantity
            total_amount += item_total
            
            # حفظ نسخة من بيانات المنتج
            sale_item = SaleItem(
                quantity=quantity,
                unit_price=unit_price,
                total_price=item_total,
                product_id=product.id,
                product_name=product.name_ar,
                product_sku=product.sku
            )
            sale_items.append(sale_item)
            
            product.quantity -= quantity
            
            movement = InventoryMovement(
                movement_type='out',
                quantity=quantity,
                previous_quantity=product.quantity + quantity,
                new_quantity=product.quantity,
                reason='sale',
                product_id=product.id,
                employee_id=current_user.id
            )
            db.session.add(movement)
        
        sale.total_amount = total_amount - discount_amount
        db.session.add(sale)
        db.session.flush()
        
        for sale_item in sale_items:
            sale_item.sale_id = sale.id
            db.session.add(sale_item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'sale_id': sale.id,
            'invoice_number': sale.invoice_number,
            'total_amount': float(sale.total_amount)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'حدث خطأ في معالجة البيع: {str(e)}'}), 500

# =========================
# إدارة المنتجات والمخزون


@app.route('/search_product')
def search_product():
    barcode = request.args.get('barcode')
    if not barcode:
        return jsonify({"error": "no barcode"}), 400

    product = Product.query.filter_by(barcode=barcode).first()
    if product:
        return jsonify({
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "stock": product.stock
        })
    else:
        return jsonify({"error": "not found"}), 404

# =========================
@app.route('/inventory')
@login_required
def inventory():
    if not current_user.has_permission('manage_inventory'):
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category_id', type=int)
    
    query = Product.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(
            or_(
                Product.name_ar.contains(search),
                Product.name.contains(search),
                Product.barcode.contains(search),
                Product.sku.contains(search)
            )
        )
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    products = query.order_by(Product.name_ar).paginate(
        page=page, per_page=20, error_out=False
    )
    
    categories = Category.query.all()
    
    return render_template('inventory.html', 
                         products=products, 
                         categories=categories,
                         search=search,
                         selected_category=category_id)

@app.route('/invoice/<int:sale_id>')
@login_required
def view_invoice(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('invoice.html', sale=sale)

@app.route('/print_invoice/<int:sale_id>')
@login_required
def print_invoice(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    # إذا أردت طباعة PDF استخدم الدالة create_invoice_pdf
    pdf_path = create_invoice_pdf(sale)  # دالة توليد PDF موجودة في utils.py
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"invoice_{sale.invoice_number}.pdf"
    )

@app.route('/products')
@login_required
def products():
    if not current_user.has_permission('manage_products'):
        flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category_id', type=int)
    
    query = Product.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(
            or_(
                Product.name_ar.contains(search),
                Product.name.contains(search),
                Product.barcode.contains(search),
                Product.sku.contains(search)
            )
        )
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    products = query.order_by(Product.name_ar).paginate(page=page, per_page=20, error_out=False)
    categories = Category.query.all()
    
    return render_template('products.html', products=products, categories=categories,
                           search=search, selected_category=category_id)


# =========================
# إضافة وتعديل وحذف المنتجات مع سجل كامل
# =========================
@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.has_permission('manage_products'):
        flash('ليس لديك صلاحية لإضافة المنتجات', 'error')
        return redirect(url_for('dashboard'))
    
    form = ProductForm()
    
    if form.validate_on_submit():
        category_name = form.category_name.data.strip()
        category = Category.query.filter_by(name_ar=category_name).first()
        if not category:
            category = Category(name=category_name, name_ar=category_name)
            db.session.add(category)
            db.session.commit()
        
        image_url = None
        if form.image.data:
            file = form.image.data
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(file_path)
                image_url = f"/static/uploads/{filename}"
        
        product = Product(
            name=form.name.data,
            name_ar=form.name_ar.data,
            description=form.description.data,
            barcode=form.barcode.data,
            sku=form.sku.data,
            price=form.price.data,
            cost_price=form.cost_price.data,
            quantity=form.quantity.data,
            min_quantity=form.min_quantity.data,
            is_active=True if form.is_active.data == '1' else False,
            category_id=category.id,
            image_url=image_url
        )
        
        try:
            db.session.add(product)
            db.session.commit()
            
            # سجل إضافة المنتج في InventoryMovement
            movement = InventoryMovement(
                movement_type='in',
                quantity=product.quantity,
                previous_quantity=0,
                new_quantity=product.quantity,
                reason='initial_stock',
                product_id=product.id,
                employee_id=current_user.id
            )
            db.session.add(movement)
            db.session.commit()
            
            flash(f'تم إضافة المنتج {product.name_ar} بنجاح', 'success')
            return redirect(url_for('products'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ في إضافة المنتج: {str(e)}', 'error')
    
    return render_template('add_product.html', form=form)


@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if not current_user.has_permission('manage_products'):
        flash('ليس لديك صلاحية لتعديل المنتجات', 'error')
        return redirect(url_for('dashboard'))
    
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.category_name.data = product.category.name_ar if product.category else ''
    
    if form.validate_on_submit():
        old_quantity = product.quantity
        old_price = product.price
        old_name = product.name_ar
        old_status = product.is_active
        old_category_id = product.category_id
        
        category_name = form.category_name.data.strip()
        category = Category.query.filter_by(name_ar=category_name).first()
        if not category:
            category = Category(name=category_name, name_ar=category_name)
            db.session.add(category)
            db.session.commit()
        product.category_id = category.id
        
        if form.image.data:
            file = form.image.data
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(file_path)
                product.image_url = f"/static/uploads/{filename}"
        
        form.populate_obj(product)
        product.is_active = True if form.is_active.data == '1' else False
        product.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            
            # سجل تغييرات الكمية
            if old_quantity != product.quantity:
                movement_type = 'in' if product.quantity > old_quantity else 'adjustment'
                quantity_diff = abs(product.quantity - old_quantity)
                movement = InventoryMovement(
                    movement_type=movement_type,
                    quantity=quantity_diff,
                    previous_quantity=old_quantity,
                    new_quantity=product.quantity,
                    reason='stock_adjustment',
                    product_id=product.id,
                    employee_id=current_user.id
                )
                db.session.add(movement)

            # سجل تغييرات السعر
            if old_price != product.price:
                movement = InventoryMovement(
                    movement_type='update',
                    quantity=0,
                    previous_quantity=old_price,
                    new_quantity=product.price,
                    reason='price_change',
                    product_id=product.id,
                    employee_id=current_user.id
                )
                db.session.add(movement)

            # سجل تغييرات الاسم
            if old_name != product.name_ar:
                movement = InventoryMovement(
                    movement_type='update',
                    quantity=0,
                    previous_quantity=0,
                    new_quantity=0,
                    reason=f'name_change: {old_name} → {product.name_ar}',
                    product_id=product.id,
                    employee_id=current_user.id
                )
                db.session.add(movement)

            # سجل تغييرات الحالة
            if old_status != product.is_active:
                movement = InventoryMovement(
                    movement_type='update',
                    quantity=0,
                    previous_quantity=old_status,
                    new_quantity=product.is_active,
                    reason='status_change',
                    product_id=product.id,
                    employee_id=current_user.id
                )
                db.session.add(movement)

            # سجل تغييرات الفئة
            if old_category_id != product.category_id:
                movement = InventoryMovement(
                    movement_type='update',
                    quantity=0,
                    previous_quantity=old_category_id,
                    new_quantity=product.category_id,
                    reason='category_change',
                    product_id=product.id,
                    employee_id=current_user.id
                )
                db.session.add(movement)

            db.session.commit()
            
            flash(f'تم تحديث المنتج {product.name_ar} بنجاح', 'success')
            return redirect(url_for('products'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ في تحديث المنتج: {str(e)}', 'error')
    
    return render_template('edit_product.html', form=form, product=product)


@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    if not current_user.has_permission('manage_products'):
        flash('ليس لديك صلاحية لحذف المنتجات', 'error')
        return redirect(url_for('products'))

    product = Product.query.get_or_404(product_id)
    
    try:
        if product.sale_items:
            flash('لا يمكن حذف المنتج لأنه مرتبط بمبيعات.', 'error')
            return redirect(url_for('products'))
        
        # سجل عملية الحذف في InventoryMovement قبل الحذف
        movement = InventoryMovement(
            movement_type='deleted',
            quantity=product.quantity,
            previous_quantity=product.quantity,
            new_quantity=0,
            reason='product_deleted',
            product_id=product.id,
            employee_id=current_user.id
        )
        db.session.add(movement)
        db.session.commit()

        db.session.delete(product)
        db.session.commit()
        flash(f'تم حذف المنتج {product.name_ar} بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف المنتج: {str(e)}', 'error')
    
    return redirect(url_for('products'))


# =========================
# تقارير المبيعات
# =========================
@app.route('/sales_report')
@login_required
def sales_report():
    if not current_user.has_permission('view_reports'):
        flash('ليس لديك صلاحية لعرض التقارير', 'error')
        return redirect(url_for('dashboard'))
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date:
        start_date = datetime.utcnow().date()
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = datetime.utcnow().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    sales = Sale.query.filter(
        func.date(Sale.created_at) >= start_date,
        func.date(Sale.created_at) <= end_date
    ).order_by(Sale.created_at.desc()).all()
    
    total_revenue = sum(sale.total_amount for sale in sales)
    total_transactions = len(sales)
    
    return render_template('sales_report.html',
                           sales=sales,
                           total_revenue=total_revenue,
                           total_transactions=total_transactions,
                           start_date=start_date,
                           end_date=end_date)

# =========================
# إدارة الموظفين
# =========================
@app.route('/employees', methods=['GET', 'POST'])
@login_required
def employees():
    if not current_user.has_permission('manage_employees'):
        flash('ليس لديك صلاحية لإدارة الموظفين', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')
        password = request.form.get('password')

        if not password:
            flash('كلمة المرور مطلوبة ❌', 'error')
            return redirect(url_for('employees'))

        new_employee = Employee(
            full_name=full_name,
            username=username,
            email=email,
            role=role,
            is_active=True,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_employee)
        db.session.commit()
        flash('تمت إضافة الموظف بنجاح ✅', 'success')
        return redirect(url_for('employees'))

    employees = Employee.query.all()
    return render_template('employees.html', employees=employees)

@app.route('/edit_employee/<int:employee_id>', methods=['POST'])
@login_required
def edit_employee(employee_id):
    if not current_user.has_permission('manage_employees'):
        flash('⚠️ ليس لديك صلاحية لتعديل الموظفين', 'error')
        return redirect(url_for('employees'))

    employee = Employee.query.get_or_404(employee_id)
    employee.full_name = request.form.get('full_name')
    employee.username = request.form.get('username')
    employee.email = request.form.get('email')
    employee.role = request.form.get('role')
    employee.is_active = True if request.form.get('is_active') == 'on' else employee.is_active

    new_password = request.form.get('password')
    if new_password:
        employee.password_hash = generate_password_hash(new_password)

    try:
        db.session.commit()
        flash('تم تعديل بيانات الموظف بنجاح ✅', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء التعديل: {str(e)}', 'error')

    return redirect(url_for('employees'))

@app.route("/delete_employee/<int:employee_id>", methods=["POST"])
@login_required
def delete_employee(employee_id):
    if not current_user.has_permission('manage_employees'):
        flash("ليس لديك صلاحية لحذف الموظف", "danger")
        return redirect(url_for('employees'))

    employee = Employee.query.get_or_404(employee_id)
    
    if employee.id == current_user.id:
        flash("لا يمكنك حذف نفسك", "warning")
        return redirect(url_for('employees'))
    
    db.session.delete(employee)
    db.session.commit()
    flash("تم حذف الموظف بنجاح", "success")
    return redirect(url_for('employees'))
