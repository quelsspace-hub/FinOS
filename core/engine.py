from typing import Dict, List, Optional
from datetime import datetime, timedelta
import math

class FinanceEngine:
    """Core finance engine for calculating balances, budgets, and projections."""
    
    # Smart category mapping for intelligent categorization
    CATEGORY_KEYWORDS = {
        'Food': ['supermarket', 'grocery', 'restaurant', 'cafe', 'food', 'meal', 'lunch', 'dinner', 'breakfast', 'mercado', 'restaurante'],
        'Transport': ['uber', 'taxi', 'bus', 'metro', 'gas', 'fuel', 'parking', 'car', 'transport', 'gasolina', 'combustível'],
        'Housing': ['rent', 'mortgage', 'electricity', 'water', 'internet', 'phone', 'utility', 'aluguel', 'luz', 'água', 'internet'],
        'Entertainment': ['netflix', 'spotify', 'movie', 'cinema', 'game', 'concert', 'entertainment', 'filme', 'jogo'],
        'Health': ['pharmacy', 'doctor', 'hospital', 'medicine', 'health', 'dental', 'farmácia', 'médico', 'remédio'],
        'Education': ['course', 'book', 'school', 'university', 'education', 'training', 'curso', 'livro', 'escola'],
        'Shopping': ['clothes', 'shoes', 'electronics', 'amazon', 'store', 'mall', 'shopping', 'roupa', 'sapato'],
        'Salary': ['salary', 'wage', 'paycheck', 'income', 'salary', 'salário', 'pagamento']
    }
    
    def __init__(self, db):
        self.db = db
        self.user_id = None
        self._cached_state = None
        self._last_calculation = None
    
    def set_user(self, user_id: int):
        """Set the current user context and invalidate cache."""
        self.user_id = user_id
        self._cached_state = None
        self._last_calculation = None
    
    def calculate_balance(self) -> Dict[str, float]:
        """Calculate current balance with income and expenses."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        return self.db.get_balance(self.user_id)
    
    def smart_categorize(self, description: str, category: str = None) -> str:
        """Intelligently categorize a transaction based on description."""
        if category and category != 'Other':
            return category
        
        if not description:
            return 'Other'
        
        description_lower = description.lower()
        
        for category_name, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in description_lower:
                    return category_name
        
        return 'Other'
    
    def get_transaction_summary(self, days: int = 30) -> Dict:
        """Get transaction summary for the last N days."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        transactions = self.db.get_transactions(self.user_id, limit=1000)
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_income = 0
        recent_expenses = 0
        category_breakdown = {}
        
        for trans in transactions:
            trans_date = datetime.fromisoformat(trans['date'])
            if trans_date >= cutoff_date:
                if trans['type'] == 'income':
                    recent_income += trans['amount']
                else:
                    recent_expenses += trans['amount']
                    category = trans['category'] or 'Uncategorized'
                    category_breakdown[category] = category_breakdown.get(category, 0) + trans['amount']
        
        return {
            'period_days': days,
            'recent_income': recent_income,
            'recent_expenses': recent_expenses,
            'net_flow': recent_income - recent_expenses,
            'category_breakdown': category_breakdown
        }
    
    def calculate_budget_distribution(self, income: float) -> Dict[str, float]:
        """Calculate budget distribution based on configured percentages."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        budgets = self.db.get_budgets(self.user_id)
        distribution = {}
        total_percentage = 0
        
        for budget in budgets:
            if budget['percentage']:
                distribution[budget['category']] = income * (budget['percentage'] / 100)
                total_percentage += budget['percentage']
            elif budget['limit_value']:
                distribution[budget['category']] = budget['limit_value']
        
        # Add unallocated amount
        if total_percentage < 100:
            distribution['Unallocated'] = income * ((100 - total_percentage) / 100)
        
        return distribution
    
    def check_budget_alerts(self) -> List[Dict]:
        """Check if any budget categories are over limit."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        budgets = self.db.get_budgets(self.user_id)
        category_spending = self.db.get_transactions_by_category(self.user_id)
        alerts = []
        
        for budget in budgets:
            category = budget['category']
            spent = category_spending.get(category, 0)
            
            if budget['limit_value'] and spent > budget['limit_value']:
                alerts.append({
                    'category': category,
                    'spent': spent,
                    'limit': budget['limit_value'],
                    'over_budget': spent - budget['limit_value'],
                    'percentage_used': (spent / budget['limit_value']) * 100
                })
        
        return alerts
    
    def calculate_debt_snowball(self) -> List[Dict]:
        """Calculate debt payoff order using snowball method (smallest balance first)."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        debts = self.db.get_debts(self.user_id)
        
        # Filter out paid debts
        active_debts = [d for d in debts if d['remaining_amount'] > 0]
        
        # Sort by remaining amount (smallest first) - Snowball method
        sorted_debts = sorted(active_debts, key=lambda x: x['remaining_amount'])
        
        payoff_plan = []
        for i, debt in enumerate(sorted_debts):
            payoff_plan.append({
                'id': debt['id'],
                'total_amount': debt['total_amount'],
                'remaining_amount': debt['remaining_amount'],
                'interest_rate': debt['interest_rate'],
                'priority_rank': debt['priority_rank'],
                'payoff_order': i + 1,
                'percentage_paid': ((debt['total_amount'] - debt['remaining_amount']) / debt['total_amount']) * 100 if debt['total_amount'] > 0 else 0
            })
        
        return payoff_plan
    
    def calculate_debt_payoff_timeline(self, monthly_payment: float) -> Dict:
        """Calculate timeline to pay off all debts with given monthly payment."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        debts = self.db.get_debts(self.user_id)
        active_debts = [d for d in debts if d['remaining_amount'] > 0]
        
        if not active_debts:
            return {
                'total_months': 0,
                'total_interest_paid': 0,
                'payoff_schedule': []
            }
        
        # Sort by remaining amount (snowball)
        sorted_debts = sorted(active_debts, key=lambda x: x['remaining_amount'])
        
        timeline = []
        remaining_payment = monthly_payment
        total_months = 0
        total_interest = 0
        
        for debt in sorted_debts:
            remaining = debt['remaining_amount']
            interest_rate = debt['interest_rate'] / 100 / 12  # Monthly rate
            
            debt_months = 0
            debt_interest = 0
            
            while remaining > 0.01 and remaining_payment > 0:
                # Calculate interest for this month
                monthly_interest = remaining * interest_rate
                debt_interest += monthly_interest
                total_interest += monthly_interest
                
                # Apply payment
                principal_payment = min(remaining_payment - monthly_interest, remaining)
                remaining -= principal_payment
                
                debt_months += 1
                total_months += 1
                
                timeline.append({
                    'month': total_months,
                    'debt_id': debt['id'],
                    'payment': remaining_payment,
                    'interest': monthly_interest,
                    'principal': principal_payment,
                    'remaining': remaining
                })
            
            # After paying off this debt, roll over the payment to next debt
            # (payment stays the same, now applied fully to next debt)
        
        return {
            'total_months': total_months,
            'total_interest_paid': total_interest,
            'payoff_schedule': timeline
        }
    
    def project_balance(self, months: int = 3) -> Dict:
        """Project balance for N months based on current trends."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        summary = self.get_transaction_summary(days=30)
        monthly_net = summary['net_flow']
        
        current_balance = self.calculate_balance()['balance']
        
        projections = []
        running_balance = current_balance
        
        for month in range(1, months + 1):
            running_balance += monthly_net
            projections.append({
                'month': month,
                'projected_balance': running_balance
            })
        
        return {
            'current_balance': current_balance,
            'monthly_net_flow': monthly_net,
            'projections': projections
        }
    
    def recalculate_state(self) -> Dict:
        """Recalculate all financial state after a transaction change."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        # Calculate all financial metrics
        balance = self.calculate_balance()
        summary = self.get_transaction_summary(days=30)
        budget_distribution = self.calculate_budget_distribution(balance['total_income'])
        budget_alerts = self.check_budget_alerts()
        projections = self.project_balance(months=3)
        
        # Cache the state
        self._cached_state = {
            'balance': balance,
            'summary': summary,
            'budget_distribution': budget_distribution,
            'budget_alerts': budget_alerts,
            'projections': projections,
            'last_updated': datetime.now().isoformat()
        }
        self._last_calculation = datetime.now()
        
        return self._cached_state
    
    def get_cached_state(self) -> Optional[Dict]:
        """Get cached financial state if available."""
        return self._cached_state
    
    def get_financial_health_score(self) -> Dict:
        """Calculate financial health score based on multiple factors."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        balance = self.calculate_balance()
        summary = self.get_transaction_summary(days=30)
        alerts = self.check_budget_alerts()
        
        score = 100
        factors = []
        
        # Factor 1: Positive balance
        if balance['balance'] >= 0:
            factors.append({'name': 'Positive Balance', 'impact': 0})
        else:
            penalty = min(abs(balance['balance']) / 1000, 30)
            score -= penalty
            factors.append({'name': 'Negative Balance', 'impact': -penalty})
        
        # Factor 2: Savings rate (income > expenses)
        if summary['net_flow'] >= 0:
            savings_rate = (summary['net_flow'] / summary['recent_income']) * 100 if summary['recent_income'] > 0 else 0
            bonus = min(savings_rate / 5, 20)
            score += bonus
            factors.append({'name': 'Positive Cash Flow', 'impact': bonus})
        else:
            penalty = min(abs(summary['net_flow']) / 500, 25)
            score -= penalty
            factors.append({'name': 'Negative Cash Flow', 'impact': -penalty})
        
        # Factor 3: Budget alerts
        if alerts:
            penalty = len(alerts) * 5
            score -= penalty
            factors.append({'name': 'Budget Overruns', 'impact': -penalty})
        
        score = max(0, min(100, score))
        
        return {
            'score': round(score, 1),
            'status': self._get_health_status(score),
            'factors': factors
        }
    
    def _get_health_status(self, score: float) -> str:
        """Get health status based on score."""
        if score >= 80:
            return 'Excellent'
        elif score >= 60:
            return 'Good'
        elif score >= 40:
            return 'Fair'
        elif score >= 20:
            return 'Poor'
        else:
            return 'Critical'
    
    def calculate_goals_impact(self) -> Dict:
        """Calculate the impact of goals on monthly budget."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        goals = self.db.get_goals(self.user_id)
        balance = self.calculate_balance()
        summary = self.get_transaction_summary(days=30)
        
        total_monthly_target = sum([g['monthly_target'] for g in goals if g['monthly_target']])
        monthly_net = summary['net_flow']
        
        # Calculate if goals are achievable with current cash flow
        if monthly_net > 0:
            affordability_ratio = (monthly_net / total_monthly_target) * 100 if total_monthly_target > 0 else 100
        else:
            affordability_ratio = 0
        
        return {
            'total_goals': len(goals),
            'total_monthly_target': total_monthly_target,
            'monthly_net_flow': monthly_net,
            'affordability_ratio': affordability_ratio,
            'affordable': monthly_net >= total_monthly_target,
            'shortfall': max(0, total_monthly_target - monthly_net)
        }
    
    def calculate_wishlist_affordability(self) -> List[Dict]:
        """Calculate affordability and time to achieve for wishlist items."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        wishlist = self.db.get_wishlist(self.user_id)
        summary = self.get_transaction_summary(days=30)
        monthly_net = summary['net_flow']
        
        items_analysis = []
        
        for item in wishlist:
            if item['status'] == 'achieved':
                continue
            
            price = item['price']
            
            if monthly_net > 0:
                months_to_achieve = math.ceil(price / monthly_net)
                affordable = True
            else:
                months_to_achieve = float('inf')
                affordable = False
            
            items_analysis.append({
                'id': item['id'],
                'name': item['name'],
                'price': price,
                'priority': item['priority'],
                'monthly_net': monthly_net,
                'months_to_achieve': months_to_achieve,
                'affordable': affordable,
                'estimated_date': (datetime.now() + timedelta(days=months_to_achieve * 30)).strftime('%Y-%m-%d') if affordable else None
            })
        
        # Sort by priority then by months to achieve
        items_analysis.sort(key=lambda x: (x['priority'], x['months_to_achieve']))
        
        return items_analysis
    
    def update_goal_progress(self, goal_id: int, contribution: float) -> bool:
        """Update goal progress with a contribution."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        goal = None
        goals = self.db.get_goals(self.user_id)
        for g in goals:
            if g['id'] == goal_id:
                goal = g
                break
        
        if not goal:
            return False
        
        current_progress = goal['progress'] or 0
        new_progress = min(current_progress + contribution, goal['target_value'])
        
        self.db.update_goal(goal_id, progress=new_progress)
        return True
    
    def calculate_total_goals_progress(self) -> Dict:
        """Calculate overall progress across all goals."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        goals = self.db.get_goals(self.user_id)
        
        total_target = sum([g['target_value'] for g in goals])
        total_progress = sum([g['progress'] or 0 for g in goals])
        
        if total_target > 0:
            overall_percentage = (total_progress / total_target) * 100
        else:
            overall_percentage = 0
        
        completed_goals = len([g for g in goals if g['progress'] >= g['target_value']])
        
        return {
            'total_goals': len(goals),
            'completed_goals': completed_goals,
            'total_target': total_target,
            'total_progress': total_progress,
            'overall_percentage': overall_percentage,
            'remaining': total_target - total_progress
        }
    
    def project_with_goals(self, months: int = 6) -> Dict:
        """Project balance considering goal contributions."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        goals_impact = self.calculate_goals_impact()
        base_projection = self.project_balance(months)
        
        adjusted_projections = []
        running_balance = base_projection['current_balance']
        
        for month in range(1, months + 1):
            # Subtract monthly goal contributions from net flow
            adjusted_net = base_projection['monthly_net_flow'] - goals_impact['total_monthly_target']
            running_balance += adjusted_net
            adjusted_projections.append({
                'month': month,
                'projected_balance': running_balance,
                'goal_contribution': goals_impact['total_monthly_target']
            })
        
        return {
            'current_balance': base_projection['current_balance'],
            'base_monthly_net': base_projection['monthly_net_flow'],
            'goal_monthly_contribution': goals_impact['total_monthly_target'],
            'adjusted_monthly_net': base_projection['monthly_net_flow'] - goals_impact['total_monthly_target'],
            'projections': adjusted_projections
        }
    
    def calculate_investment_returns(self, months: int = 12) -> Dict:
        """Calculate projected investment returns over N months."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        investments = self.db.get_investments(self.user_id)
        
        if not investments:
            return {
                'total_invested': 0,
                'total_value': 0,
                'total_gain': 0,
                'projections': []
            }
        
        total_invested = sum([inv['amount'] for inv in investments])
        
        projections = []
        running_value = total_invested
        
        for month in range(1, months + 1):
            # Calculate monthly return based on average performance
            avg_performance = sum([inv['performance'] for inv in investments]) / len(investments)
            monthly_return_rate = avg_performance / 100 / 12  # Annual to monthly
            
            monthly_gain = running_value * monthly_return_rate
            running_value += monthly_gain
            
            projections.append({
                'month': month,
                'value': running_value,
                'gain': running_value - total_invested,
                'monthly_gain': monthly_gain
            })
        
        return {
            'total_invested': total_invested,
            'total_value': running_value,
            'total_gain': running_value - total_invested,
            'average_performance': sum([inv['performance'] for inv in investments]) / len(investments),
            'projections': projections
        }
    
    def calculate_investment_allocation(self) -> Dict:
        """Calculate investment allocation by asset type."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        investments = self.db.get_investments(self.user_id)
        
        if not investments:
            return {}
        
        allocation = {}
        total_amount = sum([inv['amount'] for inv in investments])
        
        for inv in investments:
            asset_type = inv['asset_type']
            amount = inv['amount']
            
            if asset_type not in allocation:
                allocation[asset_type] = 0
            allocation[asset_type] += amount
        
        # Convert to percentages
        allocation_percentage = {
            asset_type: (amount / total_amount) * 100 
            for asset_type, amount in allocation.items()
        }
        
        return {
            'total_amount': total_amount,
            'allocation': allocation,
            'allocation_percentage': allocation_percentage
        }
    
    def project_with_investments(self, months: int = 12) -> Dict:
        """Project balance including investment returns."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        base_projection = self.project_balance(months)
        investment_returns = self.calculate_investment_returns(months)
        
        combined_projections = []
        
        for i in range(months):
            base_balance = base_projection['projections'][i]['projected_balance']
            investment_value = investment_returns['projections'][i]['value'] if i < len(investment_returns['projections']) else investment_returns['total_value']
            
            combined_projections.append({
                'month': i + 1,
                'cash_balance': base_balance,
                'investment_value': investment_value,
                'total_net_worth': base_balance + investment_value
            })
        
        return {
            'current_cash_balance': base_projection['current_balance'],
            'current_investment_value': investment_returns['total_invested'],
            'current_net_worth': base_projection['current_balance'] + investment_returns['total_invested'],
            'projections': combined_projections
        }
