import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from core.database import get_transactions, get_transactions_by_category, get_balance
from core.engine import FinanceEngine
from datetime import datetime, timedelta
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Visualizations - FinOS",
    page_icon="📊",
    layout="wide"
)

# Get user from session state
if 'user_id' not in st.session_state:
    st.error("Please select a user from the main dashboard first.")
    st.stop()

user_id = st.session_state['user_id']

# Initialize engine
engine = FinanceEngine(st)
engine.set_user(user_id)

st.title("📊 Financial Visualizations")
st.markdown("---")

# Get data
transactions = get_transactions(user_id, limit=1000)
category_spending = get_transactions_by_category(user_id)
balance_data = engine.calculate_balance()

# Spending by Category (Pie Chart)
st.subheader("💰 Spending by Category")

if category_spending:
    df_category = pd.DataFrame(list(category_spending.items()), columns=['Category', 'Amount'])
    fig_pie = px.pie(
        df_category, 
        values='Amount', 
        names='Category',
        title='Spending Distribution',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("No spending data available")

st.markdown("---")

# Spending by Category (Bar Chart)
st.subheader("📊 Spending by Category (Bar Chart)")

if category_spending:
    df_category_sorted = df_category.sort_values('Amount', ascending=False)
    fig_bar = px.bar(
        df_category_sorted,
        x='Category',
        y='Amount',
        title='Spending by Category',
        color='Amount',
        color_continuous_scale='Greens'
    )
    fig_bar.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.info("No spending data available")

st.markdown("---")

# Income vs Expenses Over Time
st.subheader("📈 Income vs Expenses Over Time")

if transactions:
    # Convert to DataFrame
    df = pd.DataFrame(transactions)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Group by date and type
    df_grouped = df.groupby([df['date'].dt.date, 'type'])['amount'].sum().reset_index()
    df_grouped.columns = ['date', 'type', 'amount']
    
    # Create line chart
    fig_line = px.line(
        df_grouped,
        x='date',
        y='amount',
        color='type',
        title='Income vs Expenses Over Time',
        color_discrete_map={'income': '#9ABF17', 'expense': '#D4DB7A'},
        markers=True
    )
    fig_line.update_layout(
        xaxis_title='Date',
        yaxis_title='Amount (R$)',
        legend_title='Type'
    )
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("No transaction data available")

st.markdown("---")

# Balance Evolution
st.subheader("💵 Balance Evolution")

if transactions:
    # Calculate running balance
    df = pd.DataFrame(transactions)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Add sign based on type
    df['signed_amount'] = df.apply(lambda x: x['amount'] if x['type'] == 'income' else -x['amount'], axis=1)
    
    # Calculate cumulative balance
    df['balance'] = df['signed_amount'].cumsum()
    
    # Create area chart
    fig_area = px.area(
        df,
        x='date',
        y='balance',
        title='Balance Evolution Over Time',
        color_discrete_sequence=['#9ABF17']
    )
    fig_area.update_layout(
        xaxis_title='Date',
        yaxis_title='Balance (R$)'
    )
    fig_area.add_hline(y=0, line_dash="dash", line_color="gray")
    st.plotly_chart(fig_area, use_container_width=True)
else:
    st.info("No transaction data available")

st.markdown("---")

# Monthly Summary
st.subheader("📅 Monthly Summary")

if transactions:
    df = pd.DataFrame(transactions)
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    
    monthly_summary = df.groupby(['month', 'type'])['amount'].sum().reset_index()
    monthly_summary.columns = ['month', 'type', 'amount']
    
    fig_monthly = px.bar(
        monthly_summary,
        x='month',
        y='amount',
        color='type',
        title='Monthly Income vs Expenses',
        color_discrete_map={'income': '#9ABF17', 'expense': '#D4DB7A'},
        barmode='group'
    )
    fig_monthly.update_layout(
        xaxis_title='Month',
        yaxis_title='Amount (R$)',
        legend_title='Type'
    )
    st.plotly_chart(fig_monthly, use_container_width=True)
else:
    st.info("No transaction data available")

st.markdown("---")

# Financial Health Score Gauge
st.subheader("🏆 Financial Health Score")

health_score = engine.get_financial_health_score()

fig_gauge = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = health_score['score'],
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': f"Financial Health: {health_score['status']}", 'font': {'size': 24}},
    gauge = {
        'axis': {'range': [None, 100]},
        'bar': {'color': "#9ABF17"},
        'steps': [
            {'range': [0, 20], 'color': "#FF6B6B"},
            {'range': [20, 40], 'color': "#FFD93D"},
            {'range': [40, 60], 'color': "#D4DB7A"},
            {'range': [60, 80], 'color': "#9ABF17"},
            {'range': [80, 100], 'color': "#84BF93"}
        ],
        'threshold': {
            'line': {'color': "red", 'width': 4},
            'thickness': 0.75,
            'value': 90
        }
    }
))

fig_gauge.update_layout(height=400)
st.plotly_chart(fig_gauge, use_container_width=True)

st.markdown("---")

# Budget Progress
st.subheader("📋 Budget Progress")

from core.database import get_budgets
budgets = get_budgets(user_id)

if budgets and category_spending:
    budget_data = []
    for budget in budgets:
        category = budget['category']
        spent = category_spending.get(category, 0)
        limit = budget['limit_value']
        percentage = (spent / limit * 100) if limit else 0
        
        budget_data.append({
            'Category': category,
            'Spent': spent,
            'Limit': limit,
            'Percentage': percentage
        })
    
    df_budget = pd.DataFrame(budget_data)
    
    fig_budget = px.bar(
        df_budget,
        x='Category',
        y=['Spent', 'Limit'],
        title='Budget Progress by Category',
        barmode='overlay',
        color_discrete_sequence=['#D4DB7A', '#9ABF17']
    )
    fig_budget.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_budget, use_container_width=True)
else:
    st.info("No budget data available")

st.markdown("---")

# Goals Progress
st.subheader("🎯 Goals Progress")

from core.database import get_goals
goals = get_goals(user_id)

if goals:
    goal_data = []
    for goal in goals:
        progress = goal['progress'] or 0
        target = goal['target_value']
        percentage = (progress / target * 100) if target else 0
        
        goal_data.append({
            'Goal': goal['name'],
            'Progress': progress,
            'Target': target,
            'Percentage': percentage
        })
    
    df_goals = pd.DataFrame(goal_data)
    
    fig_goals = px.bar(
        df_goals,
        x='Goal',
        y=['Progress', 'Target'],
        title='Goals Progress',
        barmode='overlay',
        color_discrete_sequence=['#84BF93', '#9ABF17']
    )
    fig_goals.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_goals, use_container_width=True)
else:
    st.info("No goals set")

st.markdown("---")

# Debt Snowball Visualization
st.subheader("💳 Debt Snowball Plan")

from core.database import get_debts
debts = get_debts(user_id)

if debts:
    snowball_plan = engine.calculate_debt_snowball()
    
    if snowball_plan:
        df_snowball = pd.DataFrame(snowball_plan)
        
        fig_snowball = px.bar(
            df_snowball,
            x='payoff_order',
            y='remaining_amount',
            title='Debt Snowball Payoff Plan',
            color='remaining_amount',
            color_continuous_scale='Reds',
            labels={'payoff_order': 'Payoff Order', 'remaining_amount': 'Remaining Amount (R$)'}
        )
        fig_snowball.update_layout(xaxis_title='Payoff Order (1 = First)')
        st.plotly_chart(fig_snowball, use_container_width=True)
    else:
        st.success("All debts are paid off! 🎉")
else:
    st.info("No debts recorded")

st.markdown("---")

# Investment Portfolio Allocation
st.subheader("📈 Investment Portfolio Allocation")

from core.database import get_investments
investments = get_investments(user_id)

if investments:
    allocation = engine.calculate_investment_allocation()
    
    if allocation:
        df_allocation = pd.DataFrame(
            list(allocation['allocation'].items()),
            columns=['Asset Type', 'Amount']
        )
        
        fig_allocation = px.pie(
            df_allocation,
            values='Amount',
            names='Asset Type',
            title='Investment Portfolio Allocation',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_allocation.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_allocation, use_container_width=True)
else:
    st.info("No investments recorded")
