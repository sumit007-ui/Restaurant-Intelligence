from functools import wraps
import os
import time
from datetime import datetime, timedelta
from flask import render_template, url_for, flash, redirect, request, jsonify, abort, current_app, send_file
from flask_login import login_user, current_user, logout_user, login_required
from io import BytesIO
from xhtml2pdf import pisa
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from extensions import db
from models import User, Dish, DailyData, Restaurant, StaffProfile, InventoryItem, Order, OrderItem
from forms import RegistrationForm, LoginForm, DishForm, DailyDataForm, RestaurantRegistrationForm, StaffForm, InventoryForm, RestaurantBrandingForm
from ml_model import DishPredictor

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access restricted to Administrators only.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'manager']:
            flash('Access restricted to Managers and Admins.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def kitchen_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'manager', 'chef']:
            flash('Access restricted to Kitchen staff.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def setup_routes(app):
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/restaurant/register', methods=['GET', 'POST'])
    def restaurant_register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = RestaurantRegistrationForm()
        if form.validate_on_submit():
            # Create Restaurant
            restaurant = Restaurant(
                name=form.restaurant_name.data,
                address=form.address.data,
                phone=form.phone.data,
                email=form.admin_email.data
            )
            db.session.add(restaurant)
            db.session.flush() # Get ID
            
            # Create Admin User
            hashed_password = generate_password_hash(form.admin_password.data)
            admin = User(
                restaurant_id=restaurant.id,
                username=form.admin_username.data,
                email=form.admin_email.data,
                password_hash=hashed_password,
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            
            flash('Restaurant and Admin account created! You can now log in.', 'success')
            return redirect(url_for('login'))
            
        return render_template('register_restaurant.html', title='Register Restaurant', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                if not user.is_active:
                    flash('Your account is deactivated. Please contact support.', 'danger')
                    return redirect(url_for('login'))
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Login unsuccessful. Please check email and password.', 'danger')

        return render_template('login.html', title='Login', form=form)

    @app.route('/logout')
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        try:
            today = datetime.now().date()
            month_ago = today - timedelta(days=30)

            # Filter data by current user's restaurant
            rid = current_user.restaurant_id
            
            # If Chef, redirect to Kitchen
            if current_user.role == 'chef':
                return redirect(url_for('kitchen_display'))
            
            # Get Stats
            total_orders = Order.query.filter_by(restaurant_id=rid).filter(Order.created_at >= month_ago).count()
            total_revenue = db.session.query(db.func.sum(Order.total_amount)).filter_by(restaurant_id=rid).filter(Order.created_at >= month_ago).scalar() or 0
            low_stock_count = InventoryItem.query.filter_by(restaurant_id=rid).filter(InventoryItem.quantity <= InventoryItem.min_stock).count()

            # Daily Trend (Last 7 days)
            daily_trend = []
            for i in range(6, -1, -1):
                d = today - timedelta(days=i)
                day_total = db.session.query(db.func.sum(Order.total_amount)).filter_by(restaurant_id=rid).filter(
                    db.func.date(Order.created_at) == d
                ).scalar() or 0
                daily_trend.append({'date': d.strftime('%m/%d'), 'revenue': float(day_total)})

            # Top selling dishes
            top_selling_query = db.session.query(
                Dish.name,
                db.func.sum(OrderItem.quantity).label('total_sold')
            ).join(OrderItem).join(Order).filter(
                Order.restaurant_id == rid,
                Order.created_at >= month_ago
            ).group_by(Dish.id).order_by(db.desc('total_sold')).limit(5).all()

            # ML suggestions 
            suggestions = []
            try:
                predictor = DishPredictor(restaurant_id=rid)
                suggestions = predictor.get_menu_optimization_suggestions()
            except Exception as e:
                current_app.logger.warning(f"Prediction skipped: {e}")

            return render_template(
                'dashboard.html',
                title='Dashboard',
                total_orders=total_orders,
                total_revenue=total_revenue,
                low_stock_count=low_stock_count,
                top_selling=top_selling_query,
                daily_trend=daily_trend,
                suggestions=suggestions,
                has_data=(total_orders > 0)
            )
        except Exception as e:
            current_app.logger.error(f"Dashboard error: {str(e)}")
            return render_template(
                'dashboard.html', 
                title='Dashboard', 
                has_data=False,
                total_orders=0,
                total_revenue=0,
                low_stock_count=0,
                top_selling=[],
                daily_trend=[],
                suggestions=[]
            )

    @app.route('/dishes', methods=['GET', 'POST'])
    @login_required
    @manager_required
    def dish_management():
        form = DishForm()
        rid = current_user.restaurant_id
        
        if form.validate_on_submit():
            dish = Dish(
                restaurant_id=rid,
                name=form.name.data,
                description=form.description.data,
                category=form.category.data,
                price=form.price.data,
                is_available=form.is_available.data
            )
            
            if form.image.data:
                upload_dir = os.path.join(current_app.root_path, 'static/uploads')
                os.makedirs(upload_dir, exist_ok=True)
                filename = secure_filename(f"{int(time.time())}_{form.image.data.filename}")
                form.image.data.save(os.path.join(upload_dir, filename))
                dish.image_url = url_for('static', filename=f'uploads/{filename}')
            
            db.session.add(dish)
            db.session.commit()
            flash('Dish added!', 'success')
            return redirect(url_for('dish_management'))
        
        dishes = Dish.query.filter_by(restaurant_id=rid).order_by(Dish.name).all()
        return render_template('dish_management.html', title='Menu Management', form=form, dishes=dishes)

    @app.route('/staff', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def staff_management():
        form = StaffForm()
        rid = current_user.restaurant_id
        
        if form.validate_on_submit():
            # Check if user already exists
            if User.query.filter((User.username == form.username.data) | (User.email == form.email.data)).first():
                flash('Username or Email already exists.', 'danger')
                return redirect(url_for('staff_management'))
                
            user = User(
                restaurant_id=rid,
                username=form.username.data,
                email=form.email.data,
                role=form.role.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()
            
            profile = StaffProfile(
                user_id=user.id,
                full_name=form.full_name.data,
                phone=form.phone.data,
                salary=form.salary.data
            )
            db.session.add(profile)
            db.session.commit()
            flash('Staff member added successfully!', 'success')
            return redirect(url_for('staff_management'))
            
        staff_list = User.query.filter_by(restaurant_id=rid).filter(User.id != current_user.id).all()
        return render_template('staff_management.html', title='Staff Management', form=form, staff_list=staff_list)

    @app.route('/staff/<int:user_id>/toggle', methods=['POST'])
    @login_required
    @admin_required
    def toggle_staff_status(user_id):
        user = User.query.filter_by(id=user_id, restaurant_id=current_user.restaurant_id).first_or_404()
        user.is_active = not user.is_active
        db.session.commit()
        flash(f'User {user.username} status updated.', 'success')
        return redirect(url_for('staff_management'))

    @app.route('/staff/<int:user_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def delete_staff(user_id):
        user = User.query.filter_by(id=user_id, restaurant_id=current_user.restaurant_id).first_or_404()
        if user == current_user:
            flash('Cannot delete yourself!', 'danger')
            return redirect(url_for('staff_management'))
            
        # Delete profile then user
        if user.staff_profile:
            db.session.delete(user.staff_profile)
        db.session.delete(user)
        db.session.commit()
        flash('Staff member deleted.', 'success')
        return redirect(url_for('staff_management'))

    @app.route('/inventory', methods=['GET', 'POST'])
    @login_required
    @manager_required
    def inventory():
        form = InventoryForm()
        rid = current_user.restaurant_id
        
        if form.validate_on_submit():
            item = InventoryItem(
                restaurant_id=rid,
                name=form.name.data,
                quantity=form.quantity.data,
                unit=form.unit.data,
                min_stock=form.min_stock.data or 0,
                cost_per_unit=form.cost_per_unit.data
            )
            db.session.add(item)
            db.session.commit()
            flash('Inventory item added!', 'success')
            return redirect(url_for('inventory'))
            
        items = InventoryItem.query.filter_by(restaurant_id=rid).all()
        return render_template('inventory.html', title='Inventory', form=form, items=items)

    @app.route('/pos', methods=['GET', 'POST'])
    @login_required
    def point_of_sale():
        rid = current_user.restaurant_id
        dishes = Dish.query.filter_by(restaurant_id=rid, is_available=True).all()
        return render_template('pos.html', title='Point of Sale', dishes=dishes)

    @app.route('/api/orders/create', methods=['POST'])
    @login_required
    def create_order():
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({'error': 'No items provided'}), 400
            
        rid = current_user.restaurant_id
        order = Order(
            restaurant_id=rid,
            user_id=current_user.id,
            total_amount=0,
            table_number=data.get('table_number', 'N/A')
        )
        db.session.add(order)
        db.session.flush()
        
        total = 0
        for item_data in data['items']:
            dish = Dish.query.filter_by(id=item_data['id'], restaurant_id=rid).first()
            if dish:
                qty = item_data.get('quantity', 1)
                item = OrderItem(
                    order_id=order.id,
                    dish_id=dish.id,
                    quantity=qty,
                    price_at_time=dish.price
                )
                total += dish.price * qty
                db.session.add(item)
        
        order.total_amount = total
        db.session.commit()
        return jsonify({'message': 'Order created', 'order_id': order.id, 'total': total})

    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        rid = current_user.restaurant_id
        restaurant = Restaurant.query.get_or_404(rid)
        form = RestaurantBrandingForm(obj=restaurant)
        
        if form.validate_on_submit():
            restaurant.name = form.name.data
            restaurant.primary_color = form.primary_color.data
            
            if form.logo.data:
                upload_dir = os.path.join(current_app.root_path, 'static/uploads/branding')
                os.makedirs(upload_dir, exist_ok=True)
                filename = secure_filename(f"logo_{rid}_{int(time.time())}_{form.logo.data.filename}")
                form.logo.data.save(os.path.join(upload_dir, filename))
                restaurant.logo_url = url_for('static', filename=f'uploads/branding/{filename}')
            
            db.session.commit()
            flash('Branding settings updated!', 'success')
            return redirect(url_for('profile'))
            
        return render_template('profile.html', title='Profile', user=current_user, form=form)

    @app.route('/kitchen')
    @login_required
    @kitchen_required
    def kitchen_display():
        rid = current_user.restaurant_id
        # Get pending, preparing, and ready orders
        orders = Order.query.filter_by(restaurant_id=rid).filter(Order.status.in_(['pending', 'preparing', 'ready'])).order_by(Order.created_at).all()
        return render_template('kitchen_display.html', title='Kitchen Display', orders=orders)

    @app.route('/api/orders/<int:order_id>/status', methods=['POST'])
    @login_required
    def update_order_status(order_id):
        rid = current_user.restaurant_id
        order = Order.query.filter_by(id=order_id, restaurant_id=rid).first_or_404()
        
        data = request.json
        new_status = data.get('status')
        if new_status in ['pending', 'preparing', 'ready', 'completed', 'cancelled']:
            order.status = new_status
            db.session.commit()
            return jsonify({'message': 'Status updated', 'status': new_status, 'order_id': order.id})
        
        return jsonify({'error': 'Invalid status'}), 400

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error_code=404, error_message="Page not found"), 404

    @app.route('/reports/revenue')
    @login_required
    @manager_required
    def generate_revenue_report():
        rid = current_user.restaurant_id
        restaurant = Restaurant.query.get_or_404(rid)
        
        # Calculate Stats (Last 30 days default)
        month_ago = datetime.utcnow() - timedelta(days=30)
        orders = Order.query.filter_by(restaurant_id=rid).filter(Order.created_at >= month_ago, Order.status == 'completed').all()
        
        total_revenue = sum(o.total_amount for o in orders)
        total_orders = len(orders)
        
        # Top Selling Dishes
        top_selling = db.session.query(
            Dish.name, 
            db.func.sum(OrderItem.quantity).label('total_qty'),
            db.func.sum(OrderItem.quantity * OrderItem.price_at_time).label('revenue')
        ).join(OrderItem).join(Order).filter(
            Order.restaurant_id == rid,
            Order.status == 'completed',
            Order.created_at >= month_ago
        ).group_by(Dish.id).order_by(db.text('total_qty DESC')).limit(5).all()

        # Pre-render complete style attributes to completely bypass IDE CSS linter errors
        bcolor = restaurant.primary_color or '#6a11cb'
        styles = {
            'color': f'style="color: {bcolor};"',
            'bg': f'style="background-color: {bcolor};"',
            'border': f'style="border-bottom: 2pt solid {bcolor};"'
        }

        html = render_template(
            'report_template.html',
            restaurant=restaurant,
            total_revenue=total_revenue,
            total_orders=total_orders,
            top_selling=top_selling,
            report_date=datetime.now().strftime('%Y-%m-%d %H:%M'),
            period="Last 30 Days",
            s=styles
        )
        
        return create_pdf(html)

    def create_pdf(html_content):
        def link_callback(uri, rel):
            """
            Convert HTML URIs to absolute system paths so xhtml2pdf can find those files
            """
            # use short variable names
            static_url = url_for('static', filename='')
            if uri.startswith(static_url):
                path = os.path.join(current_app.root_path, 'static', uri.replace(static_url, ""))
            else:
                path = uri
            return path

        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html_content.encode("UTF-8")), result, link_callback=link_callback)
        if not pdf.err:
            result.seek(0)
            return send_file(result, download_name=f"Revenue_Report_{datetime.now().strftime('%Y%m%d')}.pdf", as_attachment=True)
        return jsonify({"error": "PDF generation failed"}), 500
