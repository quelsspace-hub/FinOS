import streamlit as st
from core.database import (
    get_budgets, create_budget, get_transactions_by_category, get_balance
)
from core.engine import FinanceEngine

# Page configuration
st.set_page_config(
    page_title="Budget - FinOS",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .budget-card {
        background-color: #AED9C5;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    
    .progress-bar {
        background-color: #DDECF1;
        border-radius: 8px;
        height: 20px;
        overflow: hidden;
    }
    
    .progress-fill {
        background-color: #9ABF17;
        height: 100%;
        transition: width 0.3s ease;
    }
    
    .progress-fill-warning {
        background-color: #D4DB7A;
        height: 100%;
        transition: width 0.3s ease;
    }
    
    .progress-fill-danger {
        background-color: #FF6B6B;
        height: 100%;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# Get user from session state
if 'user_id' not in st.session_state:
    st.error("Please select a user from the main dashboard first.")
    st.stop()

user_id = st.session_state['user_id']

# Initialize engine
engine = FinanceEngine(st)
engine.set_user(user_id)

st.title("📊 Budget Management")
st.markdown("---")

# Get current balance for budget distribution
balance_data = get_balance(user_id)
monthly_income = balance_data['total_income']

# Create budget form
with st.expander("➕ Create/Update Budget Category", expanded=False):
    with st.form("budget_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            category = st.selectbox(
                "Category",
                ["Food", "Transport", "Housing", "Entertainment", 
                 "Health", "Education", "Shopping", "Other"]
            )
        
        with col2:
            budget_type = st.radio("Budget Type", ["Percentage", "Fixed Value"])
        
        with col3:
            if budget_type == "Percentage":
                value = st.number_input("Percentage (%)", min_value=0, max_value=100, value=10)
            else:
                value = st.number_input("Fixed Value (R$)", min_value=0.0, step=10.0, value=100.0)
        
        submitted = st.form_submit_button("Save Budget")
        
        if submitted:
            if budget_type == "Percentage":
                create_budget(user_id, category, percentage=value)
            else:
                create_budget(user_id, category, limit_value=value)
            st.success(f"Budget for {category} saved!")
            st.rerun()

# Display current budgets
st.subheader("Current Budget Distribution")

budgets = get_budgets(user_id)
category_spending = get_transactions_by_category(user_id)

if budgets:
    # Calculate budget distribution
    budget_dist = engine.calculate_budget_distribution(monthly_income)
    
    # Display budget cards
    for budget in budgets:
        category = budget['category']
        spent = category_spending.get(category, 0)
        
        with st.container():
            st.markdown('<div class="budget-card">', unsafe_allow_html=True)
            
            col_left, col_right = st.columns([2, 1])
            
            with col_left:
                st.markdown(f"### {category}")
                
                if budget['percentage']:
                    limit = monthly_income * (budget['percentage'] / 100)
                    st.caption(f"{budget['percentage']}% of income = R$ {limit:.2f}")
                elif budget['limit_value']:
                    limit = budget['limit_value']
                    st.caption(f"Fixed limit: R$ {limit:.2f}")
                else:
                    limit = 0
                    st.caption("No limit set")
            
            with col_right:
                st.metric("Spent", f"R$ {spent:.2f}")
                if limit > 0:
                    remaining = limit - spent
                    st.metric("Remaining", f"R$ {remaining:.2f}")
            
            # Progress bar
            if limit > 0:
                percentage_used = min((spent / limit) * 100, 100)
                
                if percentage_used < 70:
                    progress_class = "progress-fill"
                elif percentage_used < 90:
                    progress_class = "progress-fill-warning"
                else:
                    progress_class = "progress-fill-danger"
                
                st.markdown(f"""
                    <div class="progress-bar">
                        <div class="{progress_class}" style="width: {percentage_used}%"></div>
                    </div>
                    <small>{percentage_used:.1f}% used</small>
                """, unsafe_allow_html=True)
            else:
                st.info("No limit set for this category")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Display unallocated amount
    if 'Unallocated' in budget_dist:
        st.info(f"💡 Unallocated: R$ {budget_dist['Unallocated']:.2f} ({(budget_dist['Unallocated']/monthly_income)*100:.1f}% of income)")
    
    # Budget alerts
    alerts = engine.check_budget_alerts()
    if alerts:
        st.markdown("---")
        st.subheader("⚠️ Budget Alerts")
        for alert in alerts:
            st.error(
                f"**{alert['category']}**: Over budget by R$ {alert['over_budget']:.2f} "
                f"({alert['percentage_used']:.1f}% used)"
            )
else:
    st.info("No budgets configured yet. Create your first budget above!")

# Budget summary
st.markdown("---")
st.subheader("📈 Budget Summary")

col1, col2, col3 = st.columns(3)

with col1:
    total_budgeted = sum([b['limit_value'] for b in budgets if b['limit_value']])
    st.metric("Total Budgeted (Fixed)", f"R$ {total_budgeted:.2f}")

with col2:
    total_spent = sum(category_spending.values())
    st.metric("Total Spent", f"R$ {total_spent:.2f}")

with col3:
    health_score = engine.get_financial_health_score()
    score_color = "#9ABF17" if health_score['score'] >= 60 else "#D4DB7A"
    st.markdown(f"""
        <div style="background-color: #AED9C5; padding: 20px; border-radius: 12px; text-align: center;">
            <h3 style="color: #282900; margin: 0;">Financial Health</h3>
            <h1 style="color: {score_color}; margin: 10px 0;">{health_score['score']}</h1>
            <p style="color: #282900; margin: 0;">{health_score['status']}</p>
        </div>
    """, unsafe_allow_html=True)
