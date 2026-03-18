from datetime import datetime
from extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    logo_url = db.Column(db.String(255))
    primary_color = db.Column(db.String(7), default='#6a11cb') # Default premium purple
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    users = db.relationship('User', backref='restaurant', lazy=True)
    dishes = db.relationship('Dish', backref='restaurant', lazy=True)
    inventory = db.relationship('InventoryItem', backref='restaurant', lazy=True)
    orders = db.relationship('Order', backref='restaurant', lazy=True)

    def __repr__(self):
        return f'<Restaurant {self.name}>'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=True) # Nullable for global admins
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='staff')  # 'admin', 'manager', 'staff'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    daily_data = db.relationship('DailyData', backref='user', lazy=True)
    staff_profile = db.relationship('StaffProfile', backref='user', uselist=False, lazy=True)
    orders_placed = db.relationship('Order', backref='server', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

class StaffProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    salary = db.Column(db.Float)
    hire_date = db.Column(db.Date, default=datetime.utcnow().date())
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(100))

class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # appetizer, main course, dessert, beverage, side dish
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255))
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    daily_data = db.relationship('DailyData', backref='dish', lazy=True)
    order_items = db.relationship('OrderItem', backref='dish', lazy=True)
    
    def __repr__(self):
        return f'<Dish {self.name}>'
    
    def get_avg_sales(self):
        sales_data = DailyData.query.filter_by(dish_id=self.id).all()
        if not sales_data:
            return 0
        return sum(data.quantity_sold or 0 for data in sales_data) / len(sales_data)
    
    def get_avg_waste(self):
        waste_data = DailyData.query.filter_by(dish_id=self.id).all()
        if not waste_data:
            return 0
        return sum(data.quantity_wasted or 0 for data in waste_data) / len(waste_data)

class DailyData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.utcnow().date())
    day_of_week = db.Column(db.Integer, nullable=False)  # 0-6 (Monday-Sunday)
    time_of_day = db.Column(db.String(20), nullable=False)  # breakfast, lunch, dinner
    quantity_sold = db.Column(db.Integer, nullable=False)
    quantity_wasted = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<DailyData Dish:{self.dish_id} Date:{self.date}>'

class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=0)
    unit = db.Column(db.String(20))  # kg, liters, units
    min_stock = db.Column(db.Float, default=0)
    cost_per_unit = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    table_number = db.Column(db.String(10))
    total_amount = db.Column(db.Float, nullable=False, default=0)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    payment_method = db.Column(db.String(20)) # cash, card, online
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_at_time = db.Column(db.Float, nullable=False) # Store price in case it changes later