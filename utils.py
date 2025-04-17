import pandas as pd
from datetime import datetime, timedelta
from models import Dish, DailyData
from app import db

def generate_sales_report(start_date=None, end_date=None):
    """
    Generate a sales report for the given date range.
    
    Args:
        start_date: Start date for the report (default: 30 days ago)
        end_date: End date for the report (default: today)
    
    Returns:
        A dictionary containing sales report data
    """
    if not start_date:
        start_date = datetime.now().date() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now().date()
    
    # Query all daily data within the date range
    daily_data = DailyData.query.filter(
        DailyData.date.between(start_date, end_date)
    ).all()
    
    # Get all dishes
    dishes = {dish.id: dish for dish in Dish.query.all()}
    
    # Calculate total sales and waste
    total_sales = sum(data.quantity_sold for data in daily_data)
    total_waste = sum(data.quantity_wasted for data in daily_data)
    
    # Calculate sales by dish
    sales_by_dish = {}
    waste_by_dish = {}
    
    for data in daily_data:
        dish_id = data.dish_id
        if dish_id not in sales_by_dish:
            sales_by_dish[dish_id] = 0
            waste_by_dish[dish_id] = 0
        
        sales_by_dish[dish_id] += data.quantity_sold
        waste_by_dish[dish_id] += data.quantity_wasted
    
    # Format dish sales data
    dish_sales = []
    for dish_id, total_sold in sales_by_dish.items():
        if dish_id in dishes:
            dish = dishes[dish_id]
            dish_sales.append({
                'dish_id': dish_id,
                'dish_name': dish.name,
                'total_sold': total_sold,
                'total_wasted': waste_by_dish[dish_id],
                'waste_ratio': waste_by_dish[dish_id] / (total_sold + 1),  # +1 to avoid division by zero
                'revenue': total_sold * dish.price
            })
    
    # Calculate sales by day of week
    sales_by_dow = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    waste_by_dow = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    
    for data in daily_data:
        sales_by_dow[data.day_of_week] += data.quantity_sold
        waste_by_dow[data.day_of_week] += data.quantity_wasted
    
    # Calculate sales by time of day
    sales_by_tod = {'breakfast': 0, 'lunch': 0, 'dinner': 0}
    waste_by_tod = {'breakfast': 0, 'lunch': 0, 'dinner': 0}
    
    for data in daily_data:
        sales_by_tod[data.time_of_day] += data.quantity_sold
        waste_by_tod[data.time_of_day] += data.quantity_wasted
    
    # Format the report
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    report = {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'total_sales': total_sales,
        'total_waste': total_waste,
        'waste_ratio': total_waste / (total_sales + 1),
        'dish_sales': sorted(dish_sales, key=lambda x: x['total_sold'], reverse=True),
        'sales_by_day': [
            {'day': day_names[dow], 'sales': sales, 'waste': waste_by_dow[dow]}
            for dow, sales in sales_by_dow.items()
        ],
        'sales_by_time': [
            {'time': tod.capitalize(), 'sales': sales, 'waste': waste_by_tod[tod]}
            for tod, sales in sales_by_tod.items()
        ]
    }
    
    return report

def calculate_dish_statistics(dish_id):
    """
    Calculate comprehensive statistics for a specific dish.
    
    Args:
        dish_id: ID of the dish
    
    Returns:
        A dictionary containing dish statistics
    """
    dish = Dish.query.get(dish_id)
    if not dish:
        return None
    
    # Get all daily data for this dish
    daily_data = DailyData.query.filter_by(dish_id=dish_id).all()
    
    if not daily_data:
        return {
            'dish_id': dish_id,
            'dish_name': dish.name,
            'total_sales': 0,
            'total_waste': 0,
            'avg_daily_sales': 0,
            'avg_daily_waste': 0,
            'best_day': None,
            'best_time': None,
            'worst_day': None,
            'message': 'No data available for this dish.'
        }
    
    # Calculate total sales and waste
    total_sales = sum(data.quantity_sold for data in daily_data)
    total_waste = sum(data.quantity_wasted for data in daily_data)
    
    # Calculate average daily sales and waste
    unique_days = len(set(data.date for data in daily_data))
    avg_daily_sales = total_sales / unique_days if unique_days > 0 else 0
    avg_daily_waste = total_waste / unique_days if unique_days > 0 else 0
    
    # Calculate sales by day of week
    sales_by_dow = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    counts_by_dow = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    
    for data in daily_data:
        sales_by_dow[data.day_of_week] += data.quantity_sold
        counts_by_dow[data.day_of_week] += 1
    
    # Calculate average sales by day of week
    avg_sales_by_dow = {}
    for dow in range(7):
        if counts_by_dow[dow] > 0:
            avg_sales_by_dow[dow] = sales_by_dow[dow] / counts_by_dow[dow]
        else:
            avg_sales_by_dow[dow] = 0
    
    # Calculate sales by time of day
    sales_by_tod = {'breakfast': 0, 'lunch': 0, 'dinner': 0}
    counts_by_tod = {'breakfast': 0, 'lunch': 0, 'dinner': 0}
    
    for data in daily_data:
        sales_by_tod[data.time_of_day] += data.quantity_sold
        counts_by_tod[data.time_of_day] += 1
    
    # Calculate average sales by time of day
    avg_sales_by_tod = {}
    for tod in ['breakfast', 'lunch', 'dinner']:
        if counts_by_tod[tod] > 0:
            avg_sales_by_tod[tod] = sales_by_tod[tod] / counts_by_tod[tod]
        else:
            avg_sales_by_tod[tod] = 0
    
    # Find best day and time
    best_day = max(avg_sales_by_dow.items(), key=lambda x: x[1])[0] if avg_sales_by_dow else None
    best_time = max(avg_sales_by_tod.items(), key=lambda x: x[1])[0] if avg_sales_by_tod else None
    
    # Find worst day (least sales)
    worst_day = min(avg_sales_by_dow.items(), key=lambda x: x[1])[0] if avg_sales_by_dow else None
    
    # Format the statistics
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    stats = {
        'dish_id': dish_id,
        'dish_name': dish.name,
        'total_sales': total_sales,
        'total_waste': total_waste,
        'avg_daily_sales': round(avg_daily_sales, 2),
        'avg_daily_waste': round(avg_daily_waste, 2),
        'waste_ratio': round(total_waste / (total_sales + 1) * 100, 2),  # percentage
        'best_day': day_names[best_day] if best_day is not None else None,
        'best_time': best_time.capitalize() if best_time else None,
        'worst_day': day_names[worst_day] if worst_day is not None else None,
        'sales_by_day': [
            {'day': day_names[dow], 'avg_sales': round(avg_sales_by_dow.get(dow, 0), 2)}
            for dow in range(7)
        ],
        'sales_by_time': [
            {'time': tod.capitalize(), 'avg_sales': round(avg_sales_by_tod.get(tod, 0), 2)}
            for tod in ['breakfast', 'lunch', 'dinner']
        ]
    }
    
    return stats
