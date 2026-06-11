from typing import Dict, List, Optional
from datetime import datetime, timedelta
import statistics

class AILayer:
    """AI Layer for intelligent financial recommendations and insights."""
    
    def __init__(self, db):
        self.db = db
        self.user_id = None
    
    def set_user(self, user_id: int):
        """Set the current user context."""
        self.user_id = user_id
    
    def analyze_spending_patterns(self, days: int = 90) -> Dict:
        """Analyze spending patterns over the last N days."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        transactions = self.db.get_transactions(self.user_id, limit=1000)
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        category_spending = {}
        category_frequency = {}
        monthly_averages = {}
        
        for trans in transactions:
            trans_date = datetime.fromisoformat(trans['date'])
            if trans_date >= cutoff_date and trans['type'] == 'expense':
                category = trans['category'] or 'Uncategorized'
                amount = trans['amount']
                
                if category not in category_spending:
                    category_spending[category] = 0
                    category_frequency[category] = 0
                
                category_spending[category] += amount
                category_frequency[category] += 1
        
        # Calculate monthly averages
        for category, total in category_spending.items():
            monthly_averages[category] = total / (days / 30)
        
        # Find top spending categories
        sorted_spending = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)
        top_categories = sorted_spending[:5] if sorted_spending else []
        
        return {
            'period_days': days,
            'category_spending': category_spending,
            'category_frequency': category_frequency,
            'monthly_averages': monthly_averages,
            'top_categories': top_categories,
            'total_spending': sum(category_spending.values())
        }
    
    def detect_anomalies(self, days: int = 30) -> List[Dict]:
        """Detect unusual spending patterns or anomalies."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        transactions = self.db.get_transactions(self.user_id, limit=1000)
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_expenses = []
        for trans in transactions:
            trans_date = datetime.fromisoformat(trans['date'])
            if trans_date >= cutoff_date and trans['type'] == 'expense':
                recent_expenses.append(trans['amount'])
        
        if len(recent_expenses) < 3:
            return []
        
        # Calculate statistics
        mean = statistics.mean(recent_expenses)
        stdev = statistics.stdev(recent_expenses) if len(recent_expenses) > 1 else 0
        
        anomalies = []
        for trans in transactions:
            trans_date = datetime.fromisoformat(trans['date'])
            if trans_date >= cutoff_date and trans['type'] == 'expense':
                amount = trans['amount']
                
                # Flag expenses more than 2 standard deviations from mean
                if stdev > 0 and abs(amount - mean) > 2 * stdev:
                    anomalies.append({
                        'category': trans['category'],
                        'amount': amount,
                        'description': trans['description'],
                        'date': trans['date'],
                        'deviation': abs(amount - mean) / stdev
                    })
        
        return anomalies
    
    def generate_savings_recommendations(self) -> List[Dict]:
        """Generate personalized savings recommendations."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        recommendations = []
        
        # Analyze spending patterns
        patterns = self.analyze_spending_patterns(days=90)
        
        # Check for high-frequency categories
        for category, frequency in patterns['category_frequency'].items():
            if frequency > 10:  # More than 10 transactions in 90 days
                avg_amount = patterns['category_spending'][category] / frequency
                recommendations.append({
                    'type': 'frequency',
                    'category': category,
                    'message': f"Consider consolidating {category} expenses. You have {frequency} transactions averaging R$ {avg_amount:.2f}.",
                    'potential_savings': avg_amount * 0.1  # Assume 10% potential savings
                })
        
        # Check for high-spending categories
        for category, amount in patterns['top_categories']:
            monthly_avg = patterns['monthly_averages'].get(category, 0)
            if monthly_avg > 1000:  # More than R$ 1000 per month
                recommendations.append({
                    'type': 'high_spending',
                    'category': category,
                    'message': f"Your {category} spending is R$ {monthly_avg:.2f}/month. Consider setting a budget limit.",
                    'potential_savings': monthly_avg * 0.15  # Assume 15% potential savings
                })
        
        # Check budget alerts
        from core.engine import FinanceEngine
        engine = FinanceEngine(self.db)
        engine.set_user(self.user_id)
        budget_alerts = engine.check_budget_alerts()
        
        for alert in budget_alerts:
            recommendations.append({
                'type': 'budget_alert',
                'category': alert['category'],
                'message': f"You're over budget in {category} by R$ {alert['over_budget']:.2f}. Reduce spending to avoid further overspending.",
                'potential_savings': alert['over_budget']
            })
        
        return recommendations
    
    def generate_goal_recommendations(self) -> List[Dict]:
        """Generate recommendations for achieving financial goals."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        recommendations = []
        
        goals = self.db.get_goals(self.user_id)
        
        if not goals:
            recommendations.append({
                'type': 'no_goals',
                'message': "You haven't set any financial goals yet. Consider setting savings goals to track your progress.",
                'priority': 'high'
            })
            return recommendations
        
        from core.engine import FinanceEngine
        engine = FinanceEngine(self.db)
        engine.set_user(self.user_id)
        
        goals_impact = engine.calculate_goals_impact()
        
        if not goals_impact['affordable']:
            recommendations.append({
                'type': 'goals_unaffordable',
                'message': f"Your monthly goal contributions (R$ {goals_impact['total_monthly_target']:.2f}) exceed your available cash flow. Consider reducing monthly targets or increasing income.",
                'priority': 'high',
                'shortfall': goals_impact['shortfall']
            })
        
        # Check for goals approaching deadline
        for goal in goals:
            if goal['deadline']:
                deadline = datetime.fromisoformat(goal['deadline'])
                days_remaining = (deadline - datetime.now()).days
                
                if days_remaining < 30 and goal['progress'] < goal['target_value']:
                    remaining = goal['target_value'] - (goal['progress'] or 0)
                    recommendations.append({
                        'type': 'deadline_approaching',
                        'goal': goal['name'],
                        'message': f"Your goal '{goal['name']}' deadline is in {days_remaining} days. You need R$ {remaining:.2f} more to reach it.",
                        'priority': 'high',
                        'remaining': remaining
                    })
        
        return recommendations
    
    def generate_debt_recommendations(self) -> List[Dict]:
        """Generate recommendations for debt management."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        recommendations = []
        
        debts = self.db.get_debts(self.user_id)
        total_debt = self.db.get_total_debt(self.user_id)
        
        if not debts:
            recommendations.append({
                'type': 'no_debts',
                'message': "Congratulations! You're debt-free. Consider using available cash flow for investments.",
                'priority': 'low'
            })
            return recommendations
        
        # Check for high-interest debts
        for debt in debts:
            if debt['interest_rate'] > 15:  # More than 15% annual interest
                recommendations.append({
                    'type': 'high_interest',
                    'debt_id': debt['id'],
                    'message': f"You have a debt with {debt['interest_rate']}% interest rate. Consider prioritizing this debt for faster payoff.",
                    'priority': 'high',
                    'interest_rate': debt['interest_rate']
                })
        
        # Check debt-to-income ratio
        balance = self.db.get_balance(self.user_id)
        if total_debt['total_remaining'] > 0 and balance['total_income'] > 0:
            debt_ratio = total_debt['total_remaining'] / balance['total_income']
            if debt_ratio > 0.5:  # More than 50% of annual income
                recommendations.append({
                    'type': 'high_debt_ratio',
                    'message': f"Your debt-to-income ratio is {debt_ratio * 100:.1f}%. Consider reducing debt before taking on new financial commitments.",
                    'priority': 'medium',
                    'ratio': debt_ratio
                })
        
        return recommendations
    
    def generate_investment_recommendations(self) -> List[Dict]:
        """Generate recommendations for investment portfolio."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        recommendations = []
        
        investments = self.db.get_investments(self.user_id)
        
        if not investments:
            recommendations.append({
                'type': 'no_investments',
                'message': "You don't have any investments yet. Consider starting with low-risk options like fixed income or ETFs.",
                'priority': 'medium'
            })
            return recommendations
        
        # Check portfolio diversification
        asset_types = set(inv['asset_type'] for inv in investments)
        if len(asset_types) < 3:
            recommendations.append({
                'type': 'low_diversification',
                'message': f"Your portfolio has only {len(asset_types)} asset type(s). Consider diversifying across different asset classes to reduce risk.",
                'priority': 'medium',
                'asset_types': list(asset_types)
            })
        
        # Check for underperforming investments
        for inv in investments:
            if inv['performance'] < -10:  # More than 10% loss
                recommendations.append({
                    'type': 'underperforming',
                    'investment_id': inv['id'],
                    'message': f"Your {inv['asset_type']} investment is down {inv['performance']:.1f}%. Consider reviewing this investment.",
                    'priority': 'medium',
                    'performance': inv['performance']
                })
        
        return recommendations
    
    def generate_comprehensive_insights(self) -> Dict:
        """Generate comprehensive financial insights combining all analyses."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        insights = {
            'spending_patterns': self.analyze_spending_patterns(days=90),
            'anomalies': self.detect_anomalies(days=30),
            'savings_recommendations': self.generate_savings_recommendations(),
            'goal_recommendations': self.generate_goal_recommendations(),
            'debt_recommendations': self.generate_debt_recommendations(),
            'investment_recommendations': self.generate_investment_recommendations(),
            'generated_at': datetime.now().isoformat()
        }
        
        # Calculate overall health score
        total_recommendations = (
            len(insights['savings_recommendations']) +
            len(insights['goal_recommendations']) +
            len(insights['debt_recommendations']) +
            len(insights['investment_recommendations'])
        )
        
        high_priority = sum(
            1 for rec in insights['savings_recommendations'] + 
            insights['goal_recommendations'] + 
            insights['debt_recommendations'] + 
            insights['investment_recommendations']
            if rec.get('priority') == 'high'
        )
        
        insights['summary'] = {
            'total_recommendations': total_recommendations,
            'high_priority_count': high_priority,
            'health_status': 'Excellent' if high_priority == 0 else 'Needs Attention' if high_priority <= 2 else 'Critical'
        }
        
        return insights
