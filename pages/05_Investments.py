import streamlit as st
from core.database import (
    get_investments, create_investment, update_investment, 
    delete_investment, update_investment_performance, get_total_investments
)
from core.engine import FinanceEngine
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Investments - FinOS",
    page_icon="📈",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .investment-card {
        background-color: #AED9C5;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    
    .performance-positive {
        color: #9ABF17;
        font-weight: 600;
    }
    
    .performance-negative {
        color: #D4DB7A;
        font-weight: 600;
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

st.title("📈 Investment Portfolio")
st.markdown("---")

# Create investment form
with st.expander("➕ Add Investment", expanded=False):
    with st.form("investment_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            asset_type = st.selectbox(
                "Asset Type",
                ["Stocks", "Bonds", "Real Estate", "Crypto", "ETF", "Mutual Funds", "Fixed Income", "Other"]
            )
        
        with col2:
            amount = st.number_input("Invested Amount (R$)", min_value=0.01, step=100.0, value=1000.0)
        
        with col3:
            performance = st.number_input("Performance (% per year)", min_value=-100.0, max_value=1000.0, step=0.1, value=0.0)
        
        submitted = st.form_submit_button("Add Investment")
        
        if submitted and amount:
            create_investment(
                user_id=user_id,
                asset_type=asset_type,
                amount=amount,
                performance=performance
            )
            st.success("Investment added!")
            st.rerun()

# Display investments
st.subheader("Your Investments")

investments = get_investments(user_id)

if investments:
    # Total investment summary
    total_inv = get_total_investments(user_id)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Invested", f"R$ {total_inv['total_amount']:.2f}")
    
    with col2:
        st.metric("Current Value", f"R$ {total_inv['total_value']:.2f}")
    
    with col3:
        gain_class = "performance-positive" if total_inv['total_gain'] >= 0 else "performance-negative"
        st.markdown(f'<div class="{gain_class}">', unsafe_allow_html=True)
        st.metric("Total Gain/Loss", f"R$ {total_inv['total_gain']:.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        perf_class = "performance-positive" if total_inv['average_performance'] >= 0 else "performance-negative"
        st.markdown(f'<div class="{perf_class}">', unsafe_allow_html=True)
        st.metric("Avg Performance", f"{total_inv['average_performance']:.2f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Investment allocation
    allocation = engine.calculate_investment_allocation()
    
    if allocation:
        st.subheader("📊 Portfolio Allocation")
        
        for asset_type, percentage in allocation['allocation_percentage'].items():
            amount = allocation['allocation'][asset_type]
            st.markdown(f"**{asset_type}**: {percentage:.1f}% (R$ {amount:.2f})")
        
        st.markdown("---")
    
    # Individual investment cards
    for inv in investments:
        with st.container():
            st.markdown('<div class="investment-card">', unsafe_allow_html=True)
            
            col_left, col_right = st.columns([3, 1])
            
            with col_left:
                st.markdown(f"### {inv['asset_type']}")
                
                current_value = inv['amount'] * (1 + inv['performance'] / 100)
                gain = current_value - inv['amount']
                
                gain_class = "performance-positive" if gain >= 0 else "performance-negative"
                perf_class = "performance-positive" if inv['performance'] >= 0 else "performance-negative"
                
                st.caption(f"Invested: R$ {inv['amount']:.2f} | Current: R$ {current_value:.2f}")
                st.markdown(
                    f'<span class="{gain_class}">Gain/Loss: R$ {gain:.2f}</span> | '
                    f'<span class="{perf_class}">Performance: {inv['performance']:.2f}%</span>',
                    unsafe_allow_html=True
                )
                
                if inv['purchase_date']:
                    purchase = datetime.fromisoformat(inv['purchase_date'])
                    days_held = (datetime.now() - purchase).days
                    st.caption(f"Purchased: {inv['purchase_date'][:10]} ({days_held} days held)")
            
            with col_right:
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    new_performance = st.number_input(
                        "Update Performance (%)",
                        min_value=-100.0,
                        max_value=1000.0,
                        step=0.1,
                        value=inv['performance'],
                        key=f"perf_{inv['id']}"
                    )
                    if st.button("Update", key=f"update_{inv['id']}"):
                        update_investment_performance(inv['id'], new_performance)
                        st.success("Performance updated!")
                        st.rerun()
                
                with col_btn2:
                    if st.button("🗑️ Delete", key=f"del_{inv['id']}"):
                        delete_investment(inv['id'])
                        st.success("Investment deleted!")
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No investments yet. Start building your portfolio above!")

# Return projections
st.markdown("---")
st.subheader("📈 Return Projections")

if investments:
    projection_months = st.slider("Projection Period (months)", 3, 60, 12)
    returns = engine.calculate_investment_returns(projection_months)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Invested", f"R$ {returns['total_invested']:.2f}")
    
    with col2:
        st.metric("Projected Value", f"R$ {returns['total_value']:.2f}")
    
    with col3:
        gain_class = "performance-positive" if returns['total_gain'] >= 0 else "performance-negative"
        st.markdown(f'<div class="{gain_class}">', unsafe_allow_html=True)
        st.metric("Projected Gain", f"R$ {returns['total_gain']:.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### Monthly Projections")
    
    # Show first 12 months or all if less
    display_projections = returns['projections'][:12]
    
    for proj in display_projections:
        st.markdown(
            f"**Month {proj['month']}**: R$ {proj['value']:.2f} "
            f"(Gain: R$ {proj['gain']:.2f}, Monthly: R$ {proj['monthly_gain']:.2f})"
        )
    
    if len(returns['projections']) > 12:
        st.info(f"... and {len(returns['projections']) - 12} more months")
else:
    st.info("Add investments to see return projections.")

# Net worth projection
st.markdown("---")
st.subheader("💰 Net Worth Projection (Cash + Investments)")

if investments:
    net_worth = engine.project_with_investments(projection_months)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current Cash", f"R$ {net_worth['current_cash_balance']:.2f}")
    
    with col2:
        st.metric("Current Investments", f"R$ {net_worth['current_investment_value']:.2f}")
    
    with col3:
        st.metric("Current Net Worth", f"R$ {net_worth['current_net_worth']:.2f}")
    
    st.markdown("### Net Worth Projections")
    
    for proj in net_worth['projections'][:12]:
        st.markdown(
            f"**Month {proj['month']}**: Cash R$ {proj['cash_balance']:.2f} | "
            f"Investments R$ {proj['investment_value']:.2f} | "
            f"Net Worth R$ {proj['total_net_worth']:.2f}"
        )
else:
    st.info("Add investments to see net worth projections.")
