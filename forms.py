from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, FloatField, IntegerField, DateField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('staff', 'Staff'), ('admin', 'Admin')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose another one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use another one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class DishForm(FlaskForm):
    name = StringField('Dish Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    category = SelectField('Category', choices=[
        ('appetizer', 'Appetizer'), 
        ('main', 'Main Course'), 
        ('dessert', 'Dessert'),
        ('beverage', 'Beverage'),
        ('side', 'Side Dish')
    ])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    image = FileField('Dish Image')
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
