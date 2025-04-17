from datetime import datetime
from extensions import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='staff')  # 'admin' or 'staff'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    daily_data = db.relationship('DailyData', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

    def is_admin(self):
        return self.role == 'admin'

class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # appetizer, main, dessert, etc.
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255))  # URL to dish image
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    daily_data = db.relationship('DailyData', backref='dish', lazy=True)
    
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