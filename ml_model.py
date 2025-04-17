import pandas as pd
import numpy as np
import pickle
import os
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from models import DailyData, Dish

class DishPredictor:
    def __init__(self):
        self.sales_model = None
        self.waste_model = None
        self.sales_scaler = StandardScaler()
        self.waste_scaler = StandardScaler()
        self.label_encoders = {}
        self.model_path = 'model.pkl'
        
    def _prepare_data(self):
        """Prepare data from database for training"""
        # Get all daily data records
        daily_data = DailyData.query.all()
        
        if not daily_data or len(daily_data) < 5:  # Need at least 5 records for meaningful predictions
            return None
        
        # Convert to DataFrame
        data = []
        for record in daily_data:
            dish = Dish.query.get(record.dish_id)
            data.append({
                'dish_id': record.dish_id,
                'dish_name': dish.name,
                'dish_category': dish.category,
                'day_of_week': record.day_of_week,
                'time_of_day': record.time_of_day,
                'price': dish.price,
                'quantity_sold': record.quantity_sold,
                'quantity_wasted': record.quantity_wasted,
                'date': record.date
            })
        
        df = pd.DataFrame(data)
        
        # Label encode categorical features
        categorical_features = ['dish_category', 'time_of_day']
        for feature in categorical_features:
            le = LabelEncoder()
            df[feature + '_encoded'] = le.fit_transform(df[feature])
            self.label_encoders[feature] = le
        
        # Define sales categories - using robust method that handles duplicates
        try:
            # Try using qcut, but handle the case when there are too many duplicates
            unique_sales = df['quantity_sold'].nunique()
            if unique_sales >= 3:
                df['sales_category'] = pd.qcut(
                    df['quantity_sold'], 
                    q=3, 
                    labels=['low', 'moderate', 'high'],
                    duplicates='drop'  # Handle duplicate bin edges
                )
            else:
                # Not enough unique values, use a simpler approach
                df['sales_category'] = pd.cut(
                    df['quantity_sold'], 
                    bins=[0, df['quantity_sold'].quantile(0.33), 
                          df['quantity_sold'].quantile(0.67), 
                          df['quantity_sold'].max() + 1],
                    labels=['low', 'moderate', 'high'],
                    include_lowest=True
                )
        except Exception as e:
            # If any error occurs, fallback to a simple thresholding approach
            median_sales = df['quantity_sold'].median()
            df['sales_category'] = df['quantity_sold'].apply(
                lambda x: 'low' if x < median_sales * 0.5 else
                          'high' if x > median_sales * 1.5 else 'moderate'
            )
        
        # Define waste probability (as percentage of sales)
        df['waste_ratio'] = df['quantity_wasted'] / (df['quantity_sold'] + 1)  # +1 to avoid division by zero
        
        try:
            # Try to create waste categories with predefined bins
            df['waste_category'] = pd.cut(
                df['waste_ratio'], 
                bins=[0, 0.1, 0.3, float('inf')],  # Use infinity as the upper bound
                labels=['low', 'moderate', 'high'],
                include_lowest=True
            )
        except Exception as e:
            # If any error occurs, use a simple approach
            median_waste = df['waste_ratio'].median()
            df['waste_category'] = df['waste_ratio'].apply(
                lambda x: 'low' if x < median_waste * 0.5 else
                          'high' if x > median_waste * 1.5 else 'moderate'
            )
        
        # Features for prediction
        X_features = [
            'dish_id', 'price', 'day_of_week', 
            'dish_category_encoded', 'time_of_day_encoded'
        ]
        
        # Split for sales model
        X_sales = df[X_features]
        y_sales = df['sales_category']
        
        # Split for waste model
        X_waste = df[X_features]
        y_waste = df['waste_category']
        
        return (X_sales, y_sales), (X_waste, y_waste)
    
    def train_models(self):
        """Train sales and waste prediction models"""
        data_prepared = self._prepare_data()
        
        if data_prepared is None:
            print("Not enough data to train the models")
            return False
            
        (X_sales, y_sales), (X_waste, y_waste) = data_prepared
        
        # Scale the features
        X_sales_scaled = self.sales_scaler.fit_transform(X_sales)
        X_waste_scaled = self.waste_scaler.fit_transform(X_waste)
        
        # Train sales model
        self.sales_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.sales_model.fit(X_sales_scaled, y_sales)
        
        # Train waste model
        self.waste_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.waste_model.fit(X_waste_scaled, y_waste)
        
        # Save models
        self._save_model()
        
        return True
    
    def _save_model(self):
        """Save the trained models to disk"""
        model_data = {
            'sales_model': self.sales_model,
            'waste_model': self.waste_model,
            'sales_scaler': self.sales_scaler,
            'waste_scaler': self.waste_scaler,
            'label_encoders': self.label_encoders
        }
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self):
        """Load the trained models from disk"""
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.sales_model = model_data['sales_model']
            self.waste_model = model_data['waste_model']
            self.sales_scaler = model_data['sales_scaler']
            self.waste_scaler = model_data['waste_scaler']
            self.label_encoders = model_data['label_encoders']
            return True
        return False
    
    def predict_dish_performance(self, dish_id, day_of_week, time_of_day):
        """Predict dish sales and waste categories"""
        try:
            # Try to load or train the model
            if not self.sales_model or not self.waste_model:
                if not self.load_model():
                    if not self.train_models():
                        # Not enough data to train models, return fallback predictions
                        return self._get_fallback_prediction(dish_id, day_of_week, time_of_day)
            
            dish = Dish.query.get(dish_id)
            if not dish:
                return None
            
            # Make sure we have label encoders for these categories
            if 'dish_category' not in self.label_encoders or 'time_of_day' not in self.label_encoders:
                return self._get_fallback_prediction(dish_id, day_of_week, time_of_day)
                
            try:
                # Check if the category and time_of_day are in the label encoders
                dish_category_encoded = self.label_encoders['dish_category'].transform([dish.category])[0]
                time_of_day_encoded = self.label_encoders['time_of_day'].transform([time_of_day])[0]
            except (ValueError, KeyError) as e:
                # Category or time not in the encoder, use fallback
                return self._get_fallback_prediction(dish_id, day_of_week, time_of_day)
                
            # Prepare feature data
            features = {
                'dish_id': dish_id,
                'price': dish.price,
                'day_of_week': day_of_week,
                'dish_category_encoded': dish_category_encoded,
                'time_of_day_encoded': time_of_day_encoded
            }
            
            # Convert to DataFrame for consistent scaling
            X = pd.DataFrame([features])
            
            # Scale features
            X_sales_scaled = self.sales_scaler.transform(X)
            X_waste_scaled = self.waste_scaler.transform(X)
            
            # Make predictions
            sales_prediction = self.sales_model.predict(X_sales_scaled)[0]
            waste_prediction = self.waste_model.predict(X_waste_scaled)[0]
            
            # Get prediction probabilities
            sales_proba = self.sales_model.predict_proba(X_sales_scaled)[0]
            waste_proba = self.waste_model.predict_proba(X_waste_scaled)[0]
            
            return {
                'dish_id': dish_id,
                'dish_name': dish.name,
                'day_of_week': day_of_week,
                'time_of_day': time_of_day,
                'sales_prediction': sales_prediction,
                'sales_confidence': np.max(sales_proba) * 100,
                'waste_prediction': waste_prediction,
                'waste_confidence': np.max(waste_proba) * 100
            }
        except Exception as e:
            print(f"Error in prediction: {str(e)}")
            return self._get_fallback_prediction(dish_id, day_of_week, time_of_day)
    
    def _get_fallback_prediction(self, dish_id, day_of_week, time_of_day):
        """Provide a fallback prediction when ML model fails"""
        dish = Dish.query.get(dish_id)
        if not dish:
            return None
            
        # Base the prediction on historical data for this dish if available
        daily_data = DailyData.query.filter_by(dish_id=dish_id).all()
        
        # Default values
        sales_prediction = "moderate"
        waste_prediction = "moderate"
        sales_confidence = 50.0
        waste_confidence = 50.0
        
        if daily_data:
            # Calculate average sales and waste
            total_sales = sum(data.quantity_sold for data in daily_data)
            total_waste = sum(data.quantity_wasted for data in daily_data)
            avg_sales = total_sales / len(daily_data)
            avg_waste = total_waste / len(daily_data)
            waste_ratio = avg_waste / (avg_sales + 1)  # +1 to avoid division by zero
            
            # Simple thresholds for sales
            if avg_sales < 5:
                sales_prediction = "low"
                sales_confidence = 60.0
            elif avg_sales > 15:
                sales_prediction = "high"
                sales_confidence = 60.0
                
            # Simple thresholds for waste
            if waste_ratio < 0.1:
                waste_prediction = "low"
                waste_confidence = 60.0
            elif waste_ratio > 0.3:
                waste_prediction = "high"
                waste_confidence = 60.0
        
        # Add a slight day-of-week bias (weekend = higher sales)
        if day_of_week in [5, 6]:  # Weekend
            if sales_prediction != "high":
                sales_confidence -= 10  # Less confident in non-high predictions on weekends
            
        # Add time-of-day bias (lunch/dinner = higher sales than breakfast)
        if time_of_day in ["lunch", "dinner"]:
            if sales_prediction != "high":
                sales_confidence -= 10
        
        return {
            'dish_id': dish_id,
            'dish_name': dish.name,
            'day_of_week': day_of_week,
            'time_of_day': time_of_day,
            'sales_prediction': sales_prediction,
            'sales_confidence': sales_confidence,
            'waste_prediction': waste_prediction,
            'waste_confidence': waste_confidence
        }
    
    def get_menu_optimization_suggestions(self):
        """Generate menu optimization suggestions based on historical data"""
        dishes = Dish.query.all()
        suggestions = []
        
        days_of_week = list(range(7))  # 0-6 for Monday-Sunday
        times_of_day = ['breakfast', 'lunch', 'dinner']
        
        for dish in dishes:
            best_sales = {'sales_prediction': 'low', 'confidence': 0, 'day': None, 'time': None}
            worst_waste = {'waste_prediction': 'high', 'confidence': 0, 'day': None, 'time': None}
            
            for day in days_of_week:
                for time in times_of_day:
                    pred = self.predict_dish_performance(dish.id, day, time)
                    if pred:
                        # Track best sales conditions
                        if (pred['sales_prediction'] == 'high' and 
                            pred['sales_confidence'] > best_sales['confidence']):
                            best_sales = {
                                'sales_prediction': pred['sales_prediction'],
                                'confidence': pred['sales_confidence'],
                                'day': day,
                                'time': time
                            }
                        
                        # Track worst waste conditions
                        if (pred['waste_prediction'] == 'high' and 
                            pred['waste_confidence'] > worst_waste['confidence']):
                            worst_waste = {
                                'waste_prediction': pred['waste_prediction'],
                                'confidence': pred['waste_confidence'],
                                'day': day,
                                'time': time
                            }
            
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            suggestion = {
                'dish_id': dish.id,
                'dish_name': dish.name,
                'avg_sales': dish.get_avg_sales(),
                'avg_waste': dish.get_avg_waste(),
                'best_sales_day': day_names[best_sales['day']] if best_sales['day'] is not None else None,
                'best_sales_time': best_sales['time'],
                'worst_waste_day': day_names[worst_waste['day']] if worst_waste['day'] is not None else None,
                'worst_waste_time': worst_waste['time'],
                'recommendation': ''
            }
            
            # Generate recommendation
            if best_sales['day'] is not None and worst_waste['day'] is not None:
                if best_sales['confidence'] > 70:
                    suggestion['recommendation'] += f"Feature this dish on {day_names[best_sales['day']]} during {best_sales['time']}. "
                
                if worst_waste['confidence'] > 70:
                    suggestion['recommendation'] += f"Reduce quantity on {day_names[worst_waste['day']]} during {worst_waste['time']}."
            else:
                suggestion['recommendation'] = "Not enough data to generate meaningful recommendations."
            
            suggestions.append(suggestion)
        
        return suggestions
