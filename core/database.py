import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
import os

DATABASE_PATH = "finos.db"

def get_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize all database tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            income_profile TEXT,
            settings_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT CHECK(type IN ('income', 'expense')),
            category TEXT,
            amount REAL NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Budgets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT NOT NULL,
            percentage REAL,
            limit_value REAL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, category)
        )
    """)
    
    # Wishlist table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            priority INTEGER DEFAULT 1,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'achieved', 'cancelled')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Debts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            total_amount REAL NOT NULL,
            remaining_amount REAL NOT NULL,
            interest_rate REAL DEFAULT 0,
            priority_rank INTEGER DEFAULT 1,
            due_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Goals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            target_value REAL NOT NULL,
            monthly_target REAL,
            deadline TIMESTAMP,
            progress REAL DEFAULT 0,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Investments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            asset_type TEXT NOT NULL,
            amount REAL NOT NULL,
            performance REAL DEFAULT 0,
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()

# User CRUD operations
def create_user(name: str, income_profile: str = "medium", settings_json: str = "{}") -> int:
    """Create a new user and return the user ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, income_profile, settings_json) VALUES (?, ?, ?)",
        (name, income_profile, settings_json)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

def get_user(user_id: int) -> Optional[Dict]:
    """Get user by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_users() -> List[Dict]:
    """Get all users."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Transaction CRUD operations
def create_transaction(user_id: int, trans_type: str, category: str, amount: float, 
                       description: str = None, date: str = None) -> int:
    """Create a new transaction and return the transaction ID."""
    if date is None:
        date = datetime.now().isoformat()
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO transactions (user_id, type, category, amount, description, date) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, trans_type, category, amount, description, date)
    )
    conn.commit()
    trans_id = cursor.lastrowid
    conn.close()
    return trans_id

def get_transactions(user_id: int, limit: int = 100) -> List[Dict]:
    """Get transactions for a user, ordered by date descending."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_transaction_by_id(trans_id: int) -> Optional[Dict]:
    """Get transaction by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE id = ?", (trans_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_transaction(trans_id: int, **kwargs) -> bool:
    """Update transaction fields."""
    if not kwargs:
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    
    set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [trans_id]
    
    cursor.execute(
        f"UPDATE transactions SET {set_clause} WHERE id = ?",
        values
    )
    conn.commit()
    conn.close()
    return True

def delete_transaction(trans_id: int) -> bool:
    """Delete a transaction."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
    conn.commit()
    conn.close()
    return True

def get_balance(user_id: int) -> Dict[str, float]:
    """Calculate current balance (income - expenses)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = ? AND type = 'income'",
        (user_id,)
    )
    total_income = cursor.fetchone()[0]
    
    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = ? AND type = 'expense'",
        (user_id,)
    )
    total_expense = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense
    }

def get_transactions_by_category(user_id: int) -> Dict[str, float]:
    """Get total expenses grouped by category."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT category, COALESCE(SUM(amount), 0) as total 
           FROM transactions 
           WHERE user_id = ? AND type = 'expense' 
           GROUP BY category""",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

# Budget CRUD operations
def create_budget(user_id: int, category: str, percentage: float = None, limit_value: float = None) -> int:
    """Create a budget category."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO budgets (user_id, category, percentage, limit_value) 
           VALUES (?, ?, ?, ?)""",
        (user_id, category, percentage, limit_value)
    )
    conn.commit()
    budget_id = cursor.lastrowid
    conn.close()
    return budget_id

def get_budgets(user_id: int) -> List[Dict]:
    """Get all budgets for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM budgets WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Goals CRUD operations
def create_goal(user_id: int, name: str, target_value: float, monthly_target: float = None, 
                deadline: str = None) -> int:
    """Create a new goal and return the goal ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO goals (user_id, name, target_value, monthly_target, deadline) 
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, name, target_value, monthly_target, deadline)
    )
    conn.commit()
    goal_id = cursor.lastrowid
    conn.close()
    return goal_id

def get_goals(user_id: int) -> List[Dict]:
    """Get all goals for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM goals WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_goal(goal_id: int, **kwargs) -> bool:
    """Update goal fields."""
    if not kwargs:
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    
    set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [goal_id]
    
    cursor.execute(
        f"UPDATE goals SET {set_clause} WHERE id = ?",
        values
    )
    conn.commit()
    conn.close()
    return True

def delete_goal(goal_id: int) -> bool:
    """Delete a goal."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    conn.commit()
    conn.close()
    return True

# Wishlist CRUD operations
def create_wishlist_item(user_id: int, name: str, price: float, priority: int = 1) -> int:
    """Create a new wishlist item and return the item ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO wishlist (user_id, name, price, priority) 
           VALUES (?, ?, ?, ?)""",
        (user_id, name, price, priority)
    )
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return item_id

def get_wishlist(user_id: int) -> List[Dict]:
    """Get all wishlist items for a user, ordered by priority."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM wishlist WHERE user_id = ? ORDER BY priority ASC, id ASC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_wishlist_item(item_id: int, **kwargs) -> bool:
    """Update wishlist item fields."""
    if not kwargs:
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    
    set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [item_id]
    
    cursor.execute(
        f"UPDATE wishlist SET {set_clause} WHERE id = ?",
        values
    )
    conn.commit()
    conn.close()
    return True

def delete_wishlist_item(item_id: int) -> bool:
    """Delete a wishlist item."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM wishlist WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return True

def mark_wishlist_achieved(item_id: int) -> bool:
    """Mark a wishlist item as achieved."""
    return update_wishlist_item(item_id, status='achieved')

# Debts CRUD operations
def create_debt(user_id: int, total_amount: float, interest_rate: float = 0, 
                priority_rank: int = 1, due_date: str = None) -> int:
    """Create a new debt and return the debt ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO debts (user_id, total_amount, remaining_amount, interest_rate, priority_rank, due_date) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, total_amount, total_amount, interest_rate, priority_rank, due_date)
    )
    conn.commit()
    debt_id = cursor.lastrowid
    conn.close()
    return debt_id

def get_debts(user_id: int) -> List[Dict]:
    """Get all debts for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM debts WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_debt(debt_id: int, **kwargs) -> bool:
    """Update debt fields."""
    if not kwargs:
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    
    set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [debt_id]
    
    cursor.execute(
        f"UPDATE debts SET {set_clause} WHERE id = ?",
        values
    )
    conn.commit()
    conn.close()
    return True

def delete_debt(debt_id: int) -> bool:
    """Delete a debt."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM debts WHERE id = ?", (debt_id,))
    conn.commit()
    conn.close()
    return True

def make_debt_payment(debt_id: int, payment_amount: float) -> bool:
    """Make a payment towards a debt."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT remaining_amount FROM debts WHERE id = ?", (debt_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return False
    
    remaining = row[0]
    new_remaining = max(0, remaining - payment_amount)
    
    cursor.execute("UPDATE debts SET remaining_amount = ? WHERE id = ?", (new_remaining, debt_id))
    conn.commit()
    conn.close()
    return True

def get_total_debt(user_id: int) -> Dict[str, float]:
    """Get total debt summary for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COALESCE(SUM(total_amount), 0), COALESCE(SUM(remaining_amount), 0) FROM debts WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    return {
        'total_original': row[0],
        'total_remaining': row[1],
        'total_paid': row[0] - row[1]
    }

# Investments CRUD operations
def create_investment(user_id: int, asset_type: str, amount: float, performance: float = 0) -> int:
    """Create a new investment and return the investment ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO investments (user_id, asset_type, amount, performance) 
           VALUES (?, ?, ?, ?)""",
        (user_id, asset_type, amount, performance)
    )
    conn.commit()
    investment_id = cursor.lastrowid
    conn.close()
    return investment_id

def get_investments(user_id: int) -> List[Dict]:
    """Get all investments for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM investments WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_investment(investment_id: int, **kwargs) -> bool:
    """Update investment fields."""
    if not kwargs:
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    
    set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [investment_id]
    
    cursor.execute(
        f"UPDATE investments SET {set_clause} WHERE id = ?",
        values
    )
    conn.commit()
    conn.close()
    return True

def delete_investment(investment_id: int) -> bool:
    """Delete an investment."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM investments WHERE id = ?", (investment_id,))
    conn.commit()
    conn.close()
    return True

def update_investment_performance(investment_id: int, new_performance: float) -> bool:
    """Update investment performance percentage."""
    return update_investment(investment_id, performance=new_performance)

def get_total_investments(user_id: int) -> Dict[str, float]:
    """Get total investment summary for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0), COALESCE(AVG(performance), 0) FROM investments WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    total_amount = row[0]
    avg_performance = row[1] if row[1] is not None else 0
    
    # Calculate total value with performance
    total_value = total_amount * (1 + avg_performance / 100)
    
    return {
        'total_amount': total_amount,
        'total_value': total_value,
        'total_gain': total_value - total_amount,
        'average_performance': avg_performance
    }

# Initialize database on import
if not os.path.exists(DATABASE_PATH):
    init_database()
