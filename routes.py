import os
import time
from datetime import datetime, timedelta
from flask import render_template, url_for, flash, redirect, request, jsonify, abort, current_app
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from extensions import db
from models import User, Dish, DailyData
from forms import RegistrationForm, LoginForm, DishForm, DailyDataForm
from ml_model import DishPredictor


def setup_routes(app):
    @app.context_processor
    def inject_now():
        """Inject the current datetime into templates."""
        return {'now': datetime.now()}

    @app.route('/')
    def index():
        """Redirect to the dashboard or login page."""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """Handle user registration."""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        form = RegistrationForm()
        if form.validate_on_submit():
            if form.role.data == 'admin' and (not current_user.is_authenticated or not current_user.is_admin()):
                flash('You do not have permission to create admin accounts.', 'danger')
                return redirect(url_for('register'))

            hashed_password = generate_password_hash(form.password.data)
            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=hashed_password,
                role=form.role.data
            )
            try:
                db.session.add(user)
                db.session.commit()
                flash('Your account has been created! You can now log in.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                current_app.logger.error(f"Error creating user: {str(e)}")
                flash('An error occurred while creating your account. Please try again.', 'danger')

        return render_template('register.html', title='Register', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Handle user login."""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                next_page = request.args.get('next')
                flash('Login successful!', 'success')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Login unsuccessful. Please check email and password.', 'danger')

        return render_template('login.html', title='Login', form=form)

    @app.route('/logout')
    def logout():
        """Handle user logout."""
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Render the dashboard with analytics data."""
        try:
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)

            top_selling = []
            top_wasted = []
            daily_trend = []
            suggestions = []

            # Fetch top selling dishes
            try:
                top_selling_query = db.session.query(
                    Dish.id,
                    Dish.name,
                    db.func.sum(DailyData.quantity_sold).label('total_sold')
                ).join(DailyData).filter(
                    DailyData.date >= month_ago
                ).group_by(Dish.id).order_by(db.desc('total_sold')).limit(5).all()

                top_selling = [
                    {'id': dish[0], 'name': dish[1], 'total_sold': dish[2]}
                    for dish in top_selling_query
                ]
            except Exception as e:
                current_app.logger.error(f"Error fetching top selling dishes: {str(e)}")

            # Fetch top wasted dishes
            try:
                top_wasted_query = db.session.query(
                    Dish.id,
                    Dish.name,
                    db.func.sum(DailyData.quantity_wasted).label('total_wasted')
                ).join(DailyData).filter(
                    DailyData.date >= month_ago
                ).group_by(Dish.id).order_by(db.desc('total_wasted')).limit(5).all()

                top_wasted = [
                    {'id': dish[0], 'name': dish[1], 'total_wasted': dish[2]}
                    for dish in top_wasted_query
                ]
            except Exception as e:
                current_app.logger.error(f"Error fetching top wasted dishes: {str(e)}")

            # Fetch daily sales trends
            try:
                daily_trend_query = db.session.query(
                    DailyData.date,
                    db.func.sum(DailyData.quantity_sold).label('total_sold')
                ).filter(
                    DailyData.date >= week_ago
                ).group_by(DailyData.date).order_by(DailyData.date).all()

                daily_trend = [
                    {'date': trend[0].strftime('%Y-%m-%d'), 'total_sold': trend[1]}
                    for trend in daily_trend_query
                ]
            except Exception as e:
                current_app.logger.error(f"Error fetching daily trends: {str(e)}")

            # Fetch ML-powered suggestions
            try:
                predictor = DishPredictor()
                suggestions = predictor.get_menu_optimization_suggestions()
            except Exception as e:
                current_app.logger.error(f"Error generating ML predictions: {str(e)}")

            return render_template(
                'dashboard.html',
                title='Dashboard',
                top_selling=top_selling,
                top_wasted=top_wasted,
                daily_trend=daily_trend,
                suggestions=suggestions
            )
        except Exception as e:
            current_app.logger.error(f"Dashboard error: {str(e)}")
            flash('An error occurred while loading the dashboard. Please try again later.', 'danger')
            return render_template('dashboard.html', title='Dashboard', has_data=False)

    @app.route('/dishes', methods=['GET', 'POST'])
    @login_required
    def dish_management():
        form = DishForm()
        if form.validate_on_submit():
            # Set a more attractive default image based on the category
            default_images = {
                'appetizer': 'salad.jpg',
                'main': 'steak.jpg',
                'dessert': 'pasta.jpg',  # Using pasta as dessert for now
                'beverage': 'coffee.jpg',
                'side': 'pizza.jpg'
            }
            
            category = form.category.data
            default_image = default_images.get(category, 'pizza.jpg')
            
            dish = Dish(
                name=form.name.data,
                description=form.description.data,
                category=form.category.data,
                price=form.price.data,
                image_url=url_for('static', filename=f'uploads/{default_image}')
            )
            
            # Handle image upload
            if form.image.data:
                try:
                    # Ensure uploads directory exists
                    upload_dir = os.path.join(current_app.root_path, 'static/uploads')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Save the file with a unique name
                    filename = secure_filename(form.image.data.filename)
                    # Add timestamp to ensure uniqueness
                    filename = f"{int(time.time())}_{filename}"
                    
                    form.image.data.save(os.path.join(upload_dir, filename))
                    dish.image_url = url_for('static', filename=f'uploads/{filename}')
                except Exception as e:
                    current_app.logger.error(f"Error saving image: {str(e)}")
                    flash(f'Error uploading image: {str(e)}', 'error')
            
            db.session.add(dish)
            db.session.commit()
            flash('Dish added successfully!', 'success')
            return redirect(url_for('dish_management'))
        
        dishes = Dish.query.order_by(Dish.name).all()
        return render_template('dish_management.html', title='Dish Management', form=form, dishes=dishes)
    
    @app.route('/dishes/<int:dish_id>')
    @login_required
    def dish_details(dish_id):
        dish = Dish.query.get_or_404(dish_id)
        
        # Get historical data
        daily_data = DailyData.query.filter_by(dish_id=dish_id).order_by(DailyData.date.desc()).all()
        
        # Get ML predictions
        predictor = DishPredictor()
        predictions = []
        
        # Predict for all combinations of day and time
        days = list(range(7))  # 0-6 (Monday-Sunday)
        times = ['breakfast', 'lunch', 'dinner']
        
        for day in days:
            for time in times:
                pred = predictor.predict_dish_performance(dish_id, day, time)
                if pred:
                    # Convert day number to name
                    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    pred['day_name'] = day_names[day]
                    predictions.append(pred)
        
        return render_template(
            'dish_details.html',
            title=f'Dish - {dish.name}',
            dish=dish,
            daily_data=daily_data,
            predictions=predictions
        )
    
    @app.route('/dishes/<int:dish_id>/delete', methods=['POST'])
    @login_required
    def delete_dish(dish_id):
        dish = Dish.query.get_or_404(dish_id)
        
        # Check if user has admin rights
        if not current_user.is_admin():
            flash('You do not have permission to delete dishes.', 'danger')
            return redirect(url_for('dish_management'))
        
        db.session.delete(dish)
        db.session.commit()
        flash('Dish has been deleted!', 'success')
        return redirect(url_for('dish_management'))
    
    @app.route('/daily-data', methods=['GET', 'POST'])
    @login_required
    def daily_data():
        form = DailyDataForm()
        
        # Populate the dish choices
        form.dish.choices = [(dish.id, dish.name) for dish in Dish.query.order_by(Dish.name).all()]
        
        if form.validate_on_submit():
            # Calculate day of week (0-6, Monday is 0)
            day_of_week = form.date.data.weekday()
            
            daily_data = DailyData(
                dish_id=form.dish.data,
                user_id=current_user.id,
                date=form.date.data,
                day_of_week=day_of_week,
                time_of_day=form.time_of_day.data,
                quantity_sold=form.quantity_sold.data,
                quantity_wasted=form.quantity_wasted.data,
                notes=form.notes.data
            )
            
            db.session.add(daily_data)
            db.session.commit()
            
            # Retrain the ML model with new data
            predictor = DishPredictor()
            predictor.train_models()
            
            flash('Daily data added successfully!', 'success')
            return redirect(url_for('daily_data'))
        
        # Pre-populate with today's date
        if request.method == 'GET':
            form.date.data = datetime.now().date()
        
        # Get recent entries
        recent_entries = DailyData.query.order_by(DailyData.created_at.desc()).limit(10).all()
        
        return render_template(
            'dish_form.html',
            title='Daily Data Entry',
            form=form,
            recent_entries=recent_entries
        )
    
    @app.route('/profile')
    @login_required
    def profile():
        # Get user's activity stats
        stats = {
            'total_entries': DailyData.query.filter_by(user_id=current_user.id).count(),
            'dishes_tracked': db.session.query(db.func.count(db.distinct(DailyData.dish_id))).filter_by(user_id=current_user.id).scalar(),
            'last_active': DailyData.query.filter_by(user_id=current_user.id).order_by(DailyData.created_at.desc()).first(),
            'recent_activity': DailyData.query.filter_by(user_id=current_user.id).order_by(DailyData.created_at.desc()).limit(5).all()
        }
        
        return render_template('profile.html', title='Profile', user=current_user, stats=stats)
    
    @app.route('/api/dish-predictions/<int:dish_id>')
    @login_required
    def api_dish_predictions(dish_id):
        day = request.args.get('day', type=int)
        time = request.args.get('time')
        
        if day is None or time is None:
            return jsonify({'error': 'Missing parameters'}), 400
        
        predictor = DishPredictor()
        prediction = predictor.predict_dish_performance(dish_id, day, time)
        
        if prediction:
            return jsonify(prediction)
        return jsonify({'error': 'Could not generate prediction'}), 400
    
    @app.route('/api/dashboard-data')
    @login_required
    def api_dashboard_data():
        today = datetime.now().date()
        month_ago = today - timedelta(days=30)
        
        # Sales by category
        sales_by_category = db.session.query(
            Dish.category,
            db.func.sum(DailyData.quantity_sold).label('total_sold')
        ).join(DailyData).filter(
            DailyData.date >= month_ago
        ).group_by(Dish.category).all()
        
        # Sales by day of week
        sales_by_day = db.session.query(
            DailyData.day_of_week,
            db.func.sum(DailyData.quantity_sold).label('total_sold')
        ).filter(
            DailyData.date >= month_ago
        ).group_by(DailyData.day_of_week).all()
        
        # Format data for charts
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        formatted_sales_by_day = {
            'labels': [day_names[day[0]] for day in sales_by_day],
            'values': [day[1] for day in sales_by_day]
        }
        
        formatted_sales_by_category = {
            'labels': [category[0] for category in sales_by_category],
            'values': [category[1] for category in sales_by_category]
        }
        
        return jsonify({
            'salesByDay': formatted_sales_by_day,
            'salesByCategory': formatted_sales_by_category
        })
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error_code=404, error_message="Page not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('error.html', error_code=500, error_message="Internal server error"), 500
