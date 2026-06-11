import streamlit as st
from core.database import (
    init_database, create_user, get_all_users, 
    create_transaction, get_transactions, get_balance,
    get_transactions_by_category, get_goals, get_wishlist, get_debts, get_total_debt, get_investments, get_total_investments
)
from core.engine import FinanceEngine

# Custom CSS for premium fintech design
st.markdown("""
<style>
    .stApp {
        background-color: #DDECF1;
    }
    
    .metric-card {
        background-color: #AED9C5;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    
    .balance-positive {
        color: #9ABF17;
        font-weight: 600;
        font-family: 'Courier New', monospace;
    }
    
    .balance-negative {
        color: #D4DB7A;
        font-weight: 600;
        font-family: 'Courier New', monospace;
    }
    
    .stButton>button {
        background-color: #9ABF17;
        color: #282900;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: 600;
    }
    
    .stButton>button:hover {
        background-color: #84BF93;
    }
    
    .stTextInput>div>div>input,
    .stSelectbox>div>div>select,
    .stNumberInput>div>div>input {
        background-color: #AED9C5;
        border-radius: 8px;
        border: 1px solid #84BF93;
    }
    
    h1, h2, h3 {
        color: #282900;
    }
    
    .stDataFrame {
        background-color: #AED9C5;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
init_database()

# Page configuration
st.set_page_config(
    page_title="FinOS - Financial Operating System",
    page_icon="💰",
    layout="wide"
)

st.title("💰 FinOS - Financial Operating System")
st.markdown("---")

# User selection sidebar
st.sidebar.header("👤 User Management")
st.sidebar.markdown("---")
st.sidebar.header("📊 Navigation")
st.sidebar.page_link("app.py", label="🏠 Dashboard", icon="🏠")
st.sidebar.page_link("pages/01_Budget.py", label="📊 Budget", icon="📊")
st.sidebar.page_link("pages/02_Goals.py", label="🎯 Goals", icon="🎯")
st.sidebar.page_link("pages/03_Wishlist.py", label="🎁 Wishlist", icon="🎁")
st.sidebar.page_link("pages/04_Debts.py", label="💳 Debts", icon="💳")
st.sidebar.page_link("pages/05_Investments.py", label="📈 Investments", icon="📈")
st.sidebar.page_link("pages/06_Insights.py", label="🤖 AI Insights", icon="🤖")
st.sidebar.page_link("pages/07_Visualizations.py", label="📊 Visualizations", icon="📊")
st.sidebar.page_link("pages/08_Reports.py", label="📄 Reports", icon="📄")
st.sidebar.markdown("---")

users = get_all_users()
if not users:
    st.sidebar.info("No users yet. Create one below!")
    with st.sidebar.form("create_user_form"):
        name = st.text_input("Name")
        income_profile = st.selectbox("Income Profile", ["low", "medium", "high"])
        submitted = st.form_submit_button("Create User")
        if submitted and name:
            user_id = create_user(name, income_profile)
            st.sidebar.success(f"User '{name}' created! ID: {user_id}")
            st.rerun()
else:
    user_options = {f"{u['name']} (ID: {u['id']})": u['id'] for u in users}
    selected_user = st.sidebar.selectbox("Select User", options=list(user_options.keys()))
    
    if selected_user:
        user_id = user_options[selected_user]
        
        # Store user_id in session state for other pages
        st.session_state['user_id'] = user_id
        
        # Initialize engine with selected user
        engine = FinanceEngine(st)
        engine.set_user(user_id)
        
        # Main dashboard
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate balance using engine
        balance_data = engine.calculate_balance()
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Income", f"R$ {balance_data['total_income']:.2f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Expenses", f"R$ {balance_data['total_expense']:.2f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            balance_class = "balance-positive" if balance_data['balance'] >= 0 else "balance-negative"
            st.markdown(f'<div class="metric-card {balance_class}">', unsafe_allow_html=True)
            st.metric("Current Balance", f"R$ {balance_data['balance']:.2f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            # Financial health score
            health_score = engine.get_financial_health_score()
            score_color = "#9ABF17" if health_score['score'] >= 60 else "#D4DB7A"
            st.markdown(f"""
                <div class="metric-card" style="text-align: center;">
                    <small style="color: #282900;">Financial Health</small><br>
                    <span style="color: {score_color}; font-size: 24px; font-weight: 600;">{health_score['score']}</span><br>
                    <small style="color: #282900;">{health_score['status']}</small>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Goals, Wishlist, Debts and Investments summary
        goals = get_goals(user_id)
        wishlist = get_wishlist(user_id)
        debts = get_debts(user_id)
        total_debt = get_total_debt(user_id)
        investments = get_investments(user_id)
        total_investments = get_total_investments(user_id)
        
        if goals or wishlist or debts or investments:
            st.subheader("🎯 Goals, Wishlist, Debts & Investments Summary")
            col_goals, col_wishlist, col_debts, col_investments = st.columns(4)
            
            with col_goals:
                if goals:
                    total_goals = len(goals)
                    completed_goals = len([g for g in goals if g['progress'] >= g['target_value']])
                    st.metric("Goals Progress", f"{completed_goals}/{total_goals}")
                else:
                    st.info("No goals set")
            
            with col_wishlist:
                if wishlist:
                    total_wishlist = len(wishlist)
                    achieved_items = len([w for w in wishlist if w['status'] == 'achieved'])
                    st.metric("Wishlist", f"{achieved_items}/{total_wishlist} achieved")
                else:
                    st.info("Wishlist empty")
            
            with col_debts:
                if total_debt['total_remaining'] > 0:
                    st.metric("Total Debt", f"R$ {total_debt['total_remaining']:.2f}")
                else:
                    st.success("Debt-free! 🎉")
            
            with col_investments:
                if total_investments['total_amount'] > 0:
                    st.metric("Investments", f"R$ {total_investments['total_value']:.2f}")
                else:
                    st.info("No investments")
            
            st.markdown("---")
        
        # Budget alerts
        budget_alerts = engine.check_budget_alerts()
        if budget_alerts:
            st.subheader("⚠️ Budget Alerts")
            for alert in budget_alerts:
                st.error(
                    f"**{alert['category']}**: Over budget by R$ {alert['over_budget']:.2f} "
                    f"({alert['percentage_used']:.1f}% used)"
                )
            st.markdown("---")
        
        # AI Insights Quick Summary
        from core.ai_layer import AILayer
        ai_layer = AILayer(st)
        ai_layer.set_user(user_id)
        
        insights = ai_layer.generate_comprehensive_insights()
        
        if insights['summary']['total_recommendations'] > 0:
            st.subheader("🤖 AI Insights Quick Summary")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Recommendations", insights['summary']['total_recommendations'])
            
            with col2:
                st.metric("High Priority", insights['summary']['high_priority_count'])
            
            if insights['summary']['high_priority_count'] > 0:
                st.warning(f"⚠️ {insights['summary']['high_priority_count']} high-priority recommendations. Check the AI Insights page for details.")
            else:
                st.success("✅ No high-priority issues detected!")
            
            st.markdown("---")
        
        # Transaction form
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("➕ Add Transaction")
            with st.form("transaction_form"):
                trans_type = st.selectbox("Type", ["income", "expense"])
                category = st.selectbox(
                    "Category",
                    ["Salary", "Food", "Transport", "Housing", "Entertainment", 
                     "Health", "Education", "Shopping", "Other"]
                )
                amount = st.number_input("Amount (R$)", min_value=0.01, step=0.01, value=100.0)
                description = st.text_input("Description (optional)")
                submitted = st.form_submit_button("Add Transaction")
                
                if submitted:
                    # Use smart categorization if category is Other
                    final_category = engine.smart_categorize(description, category)
                    
                    create_transaction(
                        user_id=user_id,
                        trans_type=trans_type,
                        category=final_category,
                        amount=amount,
                        description=description
                    )
                    
                    # Recalculate financial state
                    engine.recalculate_state()
                    
                    st.success(f"Transaction added! Categorized as: {final_category}")
                    st.rerun()
        
        with col_right:
            st.subheader("📊 Spending by Category")
            category_spending = get_transactions_by_category(user_id)
            
            if category_spending:
                for category, amount in sorted(category_spending.items(), key=lambda x: x[1], reverse=True):
                    st.markdown(f"**{category}**: R$ {amount:.2f}")
            else:
                st.info("No expenses recorded yet.")
        
        st.markdown("---")
        
        # Recent transactions
        st.subheader("📋 Recent Transactions")
        transactions = get_transactions(user_id, limit=20)
        
        if transactions:
            for trans in transactions:
                with st.container():
                    col_type, col_cat, col_amt, col_date = st.columns([1, 2, 2, 2])
                    
                    emoji = "💰" if trans['type'] == 'income' else "💸"
                    color = "#9ABF17" if trans['type'] == 'income' else "#282900"
                    
                    col_type.markdown(f"{emoji}")
                    col_cat.markdown(f"**{trans['category']}**")
                    col_amt.markdown(
                        f"<span style='color:{color}; font-family:monospace; font-weight:600;'>"
                        f"{'+' if trans['type'] == 'income' else '-'}R$ {trans['amount']:.2f}</span>",
                        unsafe_allow_html=True
                    )
                    col_date.markdown(f"<small>{trans['date'][:10]}</small>", unsafe_allow_html=True)
                    
                    if trans['description']:
                        st.caption(trans['description'])
                    
                    st.markdown("---")
        else:
            st.info("No transactions yet. Add your first transaction above!")
    
    # Create new user button
    with st.sidebar.expander("Create New User"):
        with st.form("create_user_form_sidebar"):
            new_name = st.text_input("New User Name")
            new_income_profile = st.selectbox("Income Profile", ["low", "medium", "high"])
            submitted = st.form_submit_button("Create")
            if submitted and new_name:
                new_user_id = create_user(new_name, new_income_profile)
                st.sidebar.success(f"User '{new_name}' created!")
                st.rerun()

# Footer
st.markdown("---")
st.markdown("<small>FinOS v1.0 - Phase 8: Report Export (COMPLETE)</small>", unsafe_allow_html=True)
