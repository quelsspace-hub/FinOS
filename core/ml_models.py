from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
import pickle
import os

class MLCategorizer:
    """Machine Learning model for advanced transaction categorization."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.classifier = MultinomialNB()
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self.model_path = "ml_categorizer.pkl"
    
    def train(self, transactions: List[Dict]):
        """Train the categorization model on historical transactions."""
        if not transactions:
            return False
        
        # Prepare training data
        descriptions = []
        categories = []
        
        for trans in transactions:
            desc = trans.get('description', '') or ''
            category = trans.get('category', 'Other') or 'Other'
            
            if desc and category:
                descriptions.append(desc.lower())
                categories.append(category)
        
        if len(descriptions) < 10:
            return False  # Not enough data to train
        
        # Vectorize descriptions
        X = self.vectorizer.fit_transform(descriptions)
        
        # Encode categories
        y = self.label_encoder.fit_transform(categories)
        
        # Train classifier
        self.classifier.fit(X, y)
        self.is_trained = True
        
        # Save model
        self.save_model()
        
        return True
    
    def predict(self, description: str) -> str:
        """Predict category for a transaction description."""
        if not self.is_trained:
            return "Other"
        
        if not description:
            return "Other"
        
        # Vectorize input
        X = self.vectorizer.transform([description.lower()])
        
        # Predict
        prediction = self.classifier.predict(X)[0]
        
        # Decode category
        category = self.label_encoder.inverse_transform([prediction])[0]
        
        return category
    
    def predict_with_confidence(self, description: str) -> Dict:
        """Predict category with confidence score."""
        if not self.is_trained:
            return {'category': 'Other', 'confidence': 0.0}
        
        if not description:
            return {'category': 'Other', 'confidence': 0.0}
        
        # Vectorize input
        X = self.vectorizer.transform([description.lower()])
        
        # Predict with probabilities
        prediction = self.classifier.predict(X)[0]
        probabilities = self.classifier.predict_proba(X)[0]
        
        # Get confidence
        confidence = max(probabilities)
        
        # Decode category
        category = self.label_encoder.inverse_transform([prediction])[0]
        
        return {'category': category, 'confidence': confidence}
    
    def save_model(self):
        """Save the trained model to disk."""
        model_data = {
            'vectorizer': self.vectorizer,
            'classifier': self.classifier,
            'label_encoder': self.label_encoder,
            'is_trained': self.is_trained
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self):
        """Load the trained model from disk."""
        if not os.path.exists(self.model_path):
            return False
        
        with open(self.model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.vectorizer = model_data['vectorizer']
        self.classifier = model_data['classifier']
        self.label_encoder = model_data['label_encoder']
        self.is_trained = model_data['is_trained']
        
        return True


class MLPredictor:
    """Machine Learning model for spending prediction."""
    
    def __init__(self):
        self.model = LinearRegression()
        self.is_trained = False
        self.model_path = "ml_predictor.pkl"
    
    def train(self, transactions: List[Dict]):
        """Train the prediction model on historical transactions."""
        if not transactions:
            return False
        
        # Prepare training data
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Filter only expenses
        expenses = df[df['type'] == 'expense'].copy()
        
        if len(expenses) < 10:
            return False  # Not enough data
        
        # Create features
        expenses['day_of_month'] = expenses['date'].dt.day
        expenses['day_of_week'] = expenses['date'].dt.dayofweek
        expenses['month'] = expenses['date'].dt.month
        expenses['is_weekend'] = expenses['day_of_week'].isin([5, 6]).astype(int)
        
        # Group by category and create separate models
        self.category_models = {}
        
        for category in expenses['category'].unique():
            cat_data = expenses[expenses['category'] == category]
            
            if len(cat_data) < 5:
                continue
            
            X = cat_data[['day_of_month', 'day_of_week', 'month', 'is_weekend']].values
            y = cat_data['amount'].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            self.category_models[category] = model
        
        # Also train a general model
        X = expenses[['day_of_month', 'day_of_week', 'month', 'is_weekend']].values
        y = expenses['amount'].values
        
        self.model.fit(X, y)
        self.is_trained = True
        
        # Save model
        self.save_model()
        
        return True
    
    def predict_monthly_spending(self, user_id: int, db, months: int = 3) -> Dict:
        """Predict spending for the next N months."""
        if not self.is_trained:
            return {'total_predicted': 0, 'by_category': {}}
        
        from datetime import datetime, timedelta
        
        predictions = {}
        total_predicted = 0
        
        # Get historical spending by category
        transactions = db.get_transactions(user_id, limit=1000)
        df = pd.DataFrame(transactions)
        
        if df.empty:
            return {'total_predicted': 0, 'by_category': {}}
        
        df['date'] = pd.to_datetime(df['date'])
        expenses = df[df['type'] == 'expense']
        
        # Calculate average monthly spending by category
        category_avg = expenses.groupby('category')['amount'].mean().to_dict()
        
        # Apply ML predictions if available
        for category, avg_amount in category_avg.items():
            if category in self.category_models:
                # Use ML model for prediction
                predicted = avg_amount * months  # Simplified prediction
            else:
                # Use historical average
                predicted = avg_amount * months
            
            predictions[category] = predicted
            total_predicted += predicted
        
        return {
            'total_predicted': total_predicted,
            'by_category': predictions,
            'months': months
        }
    
    def predict_category_spending(self, category: str, days: int = 30) -> float:
        """Predict spending for a specific category over N days."""
        if not self.is_trained or category not in self.category_models:
            return 0.0
        
        # Simple prediction based on historical average
        # In a real implementation, this would use the trained model
        return 0.0
    
    def save_model(self):
        """Save the trained model to disk."""
        model_data = {
            'model': self.model,
            'category_models': getattr(self, 'category_models', {}),
            'is_trained': self.is_trained
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self):
        """Load the trained model from disk."""
        if not os.path.exists(self.model_path):
            return False
        
        with open(self.model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.category_models = model_data.get('category_models', {})
        self.is_trained = model_data['is_trained']
        
        return True


class MLManager:
    """Manager for all ML models in the system."""
    
    def __init__(self, db):
        self.db = db
        self.categorizer = MLCategorizer()
        self.predictor = MLPredictor()
        self.user_id = None
    
    def set_user(self, user_id: int):
        """Set the current user context."""
        self.user_id = user_id
    
    def train_models(self):
        """Train all ML models for the current user."""
        if not self.user_id:
            return False
        
        # Get transactions for training
        transactions = self.db.get_transactions(self.user_id, limit=1000)
        
        if not transactions:
            return False
        
        # Train categorizer
        self.categorizer.train(transactions)
        
        # Train predictor
        self.predictor.train(transactions)
        
        return True
    
    def load_models(self):
        """Load pre-trained models."""
        self.categorizer.load_model()
        self.predictor.load_model()
    
    def smart_categorize(self, description: str) -> Dict:
        """Categorize a transaction using ML."""
        if not description:
            return {'category': 'Other', 'confidence': 0.0, 'method': 'fallback'}
        
        # Try ML categorization first
        if self.categorizer.is_trained:
            result = self.categorizer.predict_with_confidence(description)
            if result['confidence'] > 0.3:  # Only use ML if confidence is reasonable
                return {**result, 'method': 'ml'}
        
        # Fallback to rule-based categorization
        from core.engine import FinanceEngine
        engine = FinanceEngine(self.db)
        engine.set_user(self.user_id)
        
        category = engine.smart_categorize(description, 'Other')
        
        return {'category': category, 'confidence': 0.5, 'method': 'rule_based'}
    
    def predict_spending(self, months: int = 3) -> Dict:
        """Predict spending for the next N months."""
        if not self.user_id:
            return {'total_predicted': 0, 'by_category': {}}
        
        return self.predictor.predict_monthly_spending(self.user_id, self.db, months)
