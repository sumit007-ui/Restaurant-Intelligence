from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, FloatField, IntegerField, DateField, FileField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from models import User, Restaurant

class RestaurantRegistrationForm(FlaskForm):
    restaurant_name = StringField('Restaurant Name', validators=[DataRequired(), Length(min=2, max=100)])
    admin_username = StringField('Admin Username', validators=[DataRequired(), Length(min=3, max=20)])
    admin_email = StringField('Admin Email', validators=[DataRequired(), Email()])
    admin_password = PasswordField('Admin Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('admin_password')])
    address = StringField('Address')
    phone = StringField('Phone')
    submit = SubmitField('Register Restaurant')

    def validate_admin_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose another one.')

    def validate_admin_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use another one.')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('staff', 'Staff'), ('chef', 'Chef'), ('manager', 'Manager'), ('admin', 'Admin')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose another one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use another one.')

class StaffForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Initial Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[('staff', 'Staff'), ('chef', 'Chef'), ('manager', 'Manager'), ('admin', 'Admin')])
    full_name = StringField('Full Name', validators=[DataRequired()])
    phone = StringField('Phone')
    salary = FloatField('Salary')
    submit = SubmitField('Add Staff Member')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class DishForm(FlaskForm):
    name = StringField('Dish Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    category = SelectField('Category', choices=[
        ('appetizer', 'Appetizer'), 
        ('main course', 'Main Course'), 
        ('dessert', 'Dessert'),
        ('beverage', 'Beverage'),
        ('side dish', 'Side Dish')
    ])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    image = FileField('Dish Image')
    is_available = BooleanField('Is Available', default=True)
    submit = SubmitField('Save Dish')

class DailyDataForm(FlaskForm):
    dish = SelectField('Dish', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    time_of_day = SelectField('Time of Day', choices=[
        ('breakfast', 'Breakfast'), 
        ('lunch', 'Lunch'), 
        ('dinner', 'Dinner')
    ])
    quantity_sold = IntegerField('Quantity Sold', validators=[DataRequired(), NumberRange(min=0)])
    quantity_wasted = IntegerField('Quantity Wasted', validators=[DataRequired(), NumberRange(min=0)])
    notes = TextAreaField('Notes')
    submit = SubmitField('Save Data')

class RestaurantBrandingForm(FlaskForm):
    name = StringField('Restaurant Name', validators=[DataRequired(), Length(max=100)])
    logo = FileField('Restaurant Logo')
    primary_color = StringField('Brand Primary Color (Hex Code)', validators=[Length(max=7)])
    submit = SubmitField('Update Branding')

class InventoryForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired()])
    unit = StringField('Unit (e.g., kg, L, pcs)', validators=[DataRequired()])
    min_stock = FloatField('Minimum Stock Level')
    cost_per_unit = FloatField('Cost Per Unit')
    submit = SubmitField('Save Item')
class StaffForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    phone = StringField('Phone Number')
    salary = FloatField('Monthly Salary', validators=[NumberRange(min=0)])
    role = SelectField('Role', choices=[
        ('manager', 'Manager'),
        ('chef', 'Chef'),
        ('staff', 'Waiter/Staff')
    ], validators=[DataRequired()])
    submit = SubmitField('Add Staff Member')
