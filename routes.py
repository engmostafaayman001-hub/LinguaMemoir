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

@app.route('/dashboard')
@login_required
def dashboard():
    # Get today's statistics
    today = datetime.utcnow().date()
    today_sales = Sale.query.filter(func.date(Sale.created_at) == today).all()
    today_revenue = sum(sale.total_amount for sale in today_sales)
    today_transactions = len(today_sales)
    
    # Get this week's statistics
    week_start = today - timedelta(days=today.weekday())
    week_sales = Sale.query.filter(Sale.created_at >= week_start).all()
    week_revenue = sum(sale.total_amount for sale in week_sales)
    
    # Get low stock products
    low_stock_products = Product.query.filter(
        Product.quantity <= Product.min_quantity,
        Product.is_active == True
    ).all()
    
    # Get recent sales
    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(10).all()
    
    # Get total products
    total_products = Product.query.filter_by(is_active=True).count()
    
    return render_template('dashboard.html',
                         today_revenue=today_revenue,
                         today_transactions=today_transactions,
                         week_revenue=week_revenue,
                         low_stock_products=low_stock_products,
                         recent_sales=recent_sales,
                         total_products=total_products)

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
        # Create sale record
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
            
            # Create sale item
            sale_item = SaleItem(
                quantity=quantity,
                unit_price=unit_price,
                total_price=item_total,
                product_id=product.id
            )
            sale_items.append(sale_item)
            
            # Update product quantity
            product.quantity -= quantity
            
            # Create inventory movement record
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
        db.session.flush()  # Get the sale ID
        
        # Add sale items to the sale
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
    
    products = query.order_by(Product.name_ar).paginate(
        page=page, per_page=20, error_out=False
    )
    
    categories = Category.query.all()
    
    return render_template('products.html', 
                         products=products, 
                         categories=categories,
                         search=search,
                         selected_category=category_id)

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.has_permission('manage_products'):
        flash('ليس لديك صلاحية لإضافة المنتجات', 'error')
        return redirect(url_for('dashboard'))
    
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name_ar) for c in Category.query.all()]
    
    if form.validate_on_submit():
        # Handle file upload
        image_url = None
        if form.image.data:
            file = form.image.data
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid conflicts
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
            category_id=form.category_id.data,
            image_url=image_url
        )
        
        try:
            db.session.add(product)
            db.session.commit()
            
            # Create inventory movement record
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
    
    categories = Category.query.all()
    return render_template('add_product.html', form=form, categories=categories)

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if not current_user.has_permission('manage_products'):
        flash('ليس لديك صلاحية لتعديل المنتجات', 'error')
        return redirect(url_for('dashboard'))
    
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name_ar) for c in Category.query.all()]
    
    if form.validate_on_submit():
        old_quantity = product.quantity
        
        # Handle file upload
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
        product.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            
            # Create inventory movement if quantity changed
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
                db.session.commit()
            
            flash(f'تم تحديث المنتج {product.name_ar} بنجاح', 'success')
            return redirect(url_for('products'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ في تحديث المنتج: {str(e)}', 'error')
    
    categories = Category.query.all()
    return render_template('edit_product.html', form=form, product=product, categories=categories)

@app.route('/sales_report')
@login_required
def sales_report():
    if not current_user.has_permission('view_reports'):
        flash('ليس لديك صلاحية لعرض التقارير', 'error')
        return redirect(url_for('dashboard'))
    
    # Get date range from query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Default to today if no dates provided
    if not start_date:
        start_date = datetime.utcnow().date()
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = datetime.utcnow().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Query sales within date range
    sales = Sale.query.filter(
        func.date(Sale.created_at) >= start_date,
        func.date(Sale.created_at) <= end_date
    ).order_by(Sale.created_at.desc()).all()
    
    # Calculate totals
    total_revenue = sum(sale.total_amount for sale in sales)
    total_transactions = len(sales)
    
    return render_template('sales_report.html',
                         sales=sales,
                         total_revenue=total_revenue,
                         total_transactions=total_transactions,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/employees')
@login_required
def employees():
    if not current_user.has_permission('manage_employees'):
        flash('ليس لديك صلاحية لإدارة الموظفين', 'error')
        return redirect(url_for('dashboard'))
    
    employees = Employee.query.all()
    return render_template('employees.html', employees=employees)

@app.route('/invoice/<int:sale_id>')
@login_required
def view_invoice(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('invoice.html', sale=sale)

@app.route('/print_invoice/<int:sale_id>')
@login_required
def print_invoice(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    pdf_file = create_invoice_pdf(sale)
    return send_file(pdf_file, as_attachment=True, download_name=f'invoice_{sale.invoice_number}.pdf')
