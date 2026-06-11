import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import io

class ReportGenerator:
    """Generate financial reports and export data."""
    
    def __init__(self, db):
        self.db = db
        self.user_id = None
    
    def set_user(self, user_id: int):
        """Set the current user context."""
        self.user_id = user_id
    
    def export_transactions_to_csv(self, start_date: str = None, end_date: str = None) -> str:
        """Export transactions to CSV format."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        transactions = self.db.get_transactions(self.user_id, limit=10000)
        
        # Filter by date range if provided
        if start_date or end_date:
            filtered_transactions = []
            for trans in transactions:
                trans_date = datetime.fromisoformat(trans['date'])
                if start_date and trans_date < datetime.fromisoformat(start_date):
                    continue
                if end_date and trans_date > datetime.fromisoformat(end_date):
                    continue
                filtered_transactions.append(trans)
            transactions = filtered_transactions
        
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        
        # Select and rename columns
        if not df.empty:
            df = df[['date', 'type', 'category', 'amount', 'description']]
            df.columns = ['Date', 'Type', 'Category', 'Amount', 'Description']
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        
        # Convert to CSV string
        csv_string = df.to_csv(index=False)
        
        return csv_string
    
    def export_transactions_to_excel(self, start_date: str = None, end_date: str = None) -> bytes:
        """Export transactions to Excel format."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        transactions = self.db.get_transactions(self.user_id, limit=10000)
        
        # Filter by date range if provided
        if start_date or end_date:
            filtered_transactions = []
            for trans in transactions:
                trans_date = datetime.fromisoformat(trans['date'])
                if start_date and trans_date < datetime.fromisoformat(start_date):
                    continue
                if end_date and trans_date > datetime.fromisoformat(end_date):
                    continue
                filtered_transactions.append(trans)
            transactions = filtered_transactions
        
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        
        # Select and rename columns
        if not df.empty:
            df = df[['date', 'type', 'category', 'amount', 'description']]
            df.columns = ['Date', 'Type', 'Category', 'Amount', 'Description']
            df['Date'] = pd.to_datetime(df['Date'])
        
        # Convert to Excel bytes
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Transactions', index=False)
        
        output.seek(0)
        return output.getvalue()
    
    def generate_summary_report(self, days: int = 30) -> Dict:
        """Generate a summary report for the last N days."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        from core.engine import FinanceEngine
        engine = FinanceEngine(self.db)
        engine.set_user(self.user_id)
        
        balance = engine.calculate_balance()
        summary = engine.get_transaction_summary(days=days)
        category_spending = self.db.get_transactions_by_category(self.user_id)
        health_score = engine.get_financial_health_score()
        
        return {
            'period_days': days,
            'balance': balance,
            'summary': summary,
            'category_spending': category_spending,
            'health_score': health_score,
            'generated_at': datetime.now().isoformat()
        }
    
    def export_summary_to_csv(self, days: int = 30) -> str:
        """Export summary report to CSV format."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        summary = self.generate_summary_report(days)
        
        # Create summary data
        data = {
            'Metric': [
                'Total Income',
                'Total Expenses',
                'Net Flow',
                'Current Balance',
                'Financial Health Score',
                'Health Status',
                'Period (days)'
            ],
            'Value': [
                summary['balance']['total_income'],
                summary['balance']['total_expense'],
                summary['summary']['net_flow'],
                summary['balance']['balance'],
                summary['health_score']['score'],
                summary['health_score']['status'],
                summary['period_days']
            ]
        }
        
        df = pd.DataFrame(data)
        csv_string = df.to_csv(index=False)
        
        return csv_string
    
    def export_goals_to_csv(self) -> str:
        """Export goals to CSV format."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        goals = self.db.get_goals(self.user_id)
        
        df = pd.DataFrame(goals)
        
        if not df.empty:
            df = df[['name', 'target_value', 'monthly_target', 'deadline', 'progress']]
            df.columns = ['Goal Name', 'Target Value', 'Monthly Target', 'Deadline', 'Progress']
            df['Progress %'] = (df['Progress'] / df['Target Value'] * 100).round(2)
        
        csv_string = df.to_csv(index=False)
        
        return csv_string
    
    def export_debts_to_csv(self) -> str:
        """Export debts to CSV format."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        debts = self.db.get_debts(self.user_id)
        
        df = pd.DataFrame(debts)
        
        if not df.empty:
            df = df[['total_amount', 'remaining_amount', 'interest_rate', 'priority_rank', 'due_date']]
            df.columns = ['Total Amount', 'Remaining Amount', 'Interest Rate (%)', 'Priority', 'Due Date']
            df['Paid %'] = ((df['Total Amount'] - df['Remaining Amount']) / df['Total Amount'] * 100).round(2)
        
        csv_string = df.to_csv(index=False)
        
        return csv_string
    
    def export_investments_to_csv(self) -> str:
        """Export investments to CSV format."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        investments = self.db.get_investments(self.user_id)
        
        df = pd.DataFrame(investments)
        
        if not df.empty:
            df = df[['asset_type', 'amount', 'performance', 'purchase_date']]
            df.columns = ['Asset Type', 'Invested Amount', 'Performance (%)', 'Purchase Date']
            df['Current Value'] = df['Invested Amount'] * (1 + df['Performance (%)'] / 100)
        
        csv_string = df.to_csv(index=False)
        
        return csv_string
    
    def export_budget_to_csv(self) -> str:
        """Export budget to CSV format."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        budgets = self.db.get_budgets(self.user_id)
        category_spending = self.db.get_transactions_by_category(self.user_id)
        
        budget_data = []
        for budget in budgets:
            category = budget['category']
            spent = category_spending.get(category, 0)
            limit = budget['limit_value']
            percentage = budget['percentage']
            
            budget_data.append({
                'Category': category,
                'Limit': limit,
                'Percentage': percentage,
                'Spent': spent,
                'Remaining': max(0, limit - spent) if limit else 0,
                'Used %': (spent / limit * 100) if limit else 0
            })
        
        df = pd.DataFrame(budget_data)
        csv_string = df.to_csv(index=False)
        
        return csv_string
    
    def generate_comprehensive_report(self, days: int = 30) -> Dict:
        """Generate a comprehensive report with all financial data."""
        if not self.user_id:
            raise ValueError("User ID not set")
        
        from core.engine import FinanceEngine
        from core.ai_layer import AILayer
        
        engine = FinanceEngine(self.db)
        engine.set_user(self.user_id)
        
        ai_layer = AILayer(self.db)
        ai_layer.set_user(self.user_id)
        
        return {
            'summary': self.generate_summary_report(days),
            'goals': self.db.get_goals(self.user_id),
            'debts': self.db.get_debts(self.user_id),
            'investments': self.db.get_investments(self.user_id),
            'budgets': self.db.get_budgets(self.user_id),
            'wishlist': self.db.get_wishlist(self.user_id),
            'ai_insights': ai_layer.generate_comprehensive_insights(),
            'generated_at': datetime.now().isoformat()
        }
