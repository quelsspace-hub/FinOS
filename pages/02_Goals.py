import streamlit as st
from core.database import (
    get_goals, create_goal, update_goal, delete_goal, get_balance
)
from core.engine import FinanceEngine
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Goals - FinOS",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .goal-card {
        background-color: #AED9C5;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    
    .progress-bar {
        background-color: #DDECF1;
        border-radius: 8px;
        height: 24px;
        overflow: hidden;
    }
    
    .progress-fill {
        background-color: #9ABF17;
        height: 100%;
        transition: width 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #282900;
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

st.title("🎯 Financial Goals")
st.markdown("---")

# Create goal form
with st.expander("➕ Create New Goal", expanded=False):
    with st.form("goal_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            name = st.text_input("Goal Name")
        
        with col2:
            target_value = st.number_input("Target Value (R$)", min_value=0.01, step=100.0, value=1000.0)
        
        with col3:
            monthly_target = st.number_input("Monthly Contribution (R$)", min_value=0.0, step=50.0, value=100.0)
        
        col4, col5 = st.columns(2)
        
        with col4:
            deadline = st.date_input("Deadline (optional)")
        
        with col5:
            st.empty()  # Spacer
        
        submitted = st.form_submit_button("Create Goal")
        
        if submitted and name and target_value:
            deadline_str = deadline.isoformat() if deadline else None
            create_goal(
                user_id=user_id,
                name=name,
                target_value=target_value,
                monthly_target=monthly_target,
                deadline=deadline_str
            )
            st.success(f"Goal '{name}' created!")
            st.rerun()

# Display goals
st.subheader("Current Goals")

goals = get_goals(user_id)

if goals:
    # Goals impact analysis
    goals_impact = engine.calculate_goals_impact()
    total_progress = engine.calculate_total_goals_progress()
    
    # Overall progress
    st.markdown('<div class="goal-card">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Goals", total_progress['total_goals'])
    
    with col2:
        st.metric("Completed", total_progress['completed_goals'])
    
    with col3:
        st.metric("Total Target", f"R$ {total_progress['total_target']:.2f}")
    
    with col4:
        st.metric("Overall Progress", f"{total_progress['overall_percentage']:.1f}%")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Overall progress bar
    st.markdown(f"""
        <div class="progress-bar">
            <div class="progress-fill" style="width: {total_progress['overall_percentage']}%">
                {total_progress['overall_percentage']:.1f}%
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Affordability analysis
    if goals_impact['total_monthly_target'] > 0:
        if goals_impact['affordable']:
            st.success(f"✅ Goals are affordable! Monthly net: R$ {goals_impact['monthly_net']:.2f}, Required: R$ {goals_impact['total_monthly_target']:.2f}")
        else:
            st.warning(f"⚠️ Goals exceed monthly cash flow! Shortfall: R$ {goals_impact['shortfall']:.2f}")
    
    st.markdown("---")
    
    # Individual goal cards
    for goal in goals:
        with st.container():
            st.markdown('<div class="goal-card">', unsafe_allow_html=True)
            
            col_left, col_right = st.columns([3, 1])
            
            with col_left:
                st.markdown(f"### {goal['name']}")
                
                progress = goal['progress'] or 0
                target = goal['target_value']
                percentage = (progress / target) * 100 if target > 0 else 0
                
                st.caption(f"Target: R$ {target:.2f} | Progress: R$ {progress:.2f}")
                
                if goal['monthly_target']:
                    st.caption(f"Monthly contribution: R$ {goal['monthly_target']:.2f}")
                
                if goal['deadline']:
                    deadline_date = datetime.fromisoformat(goal['deadline'])
                    days_remaining = (deadline_date - datetime.now()).days
                    st.caption(f"Deadline: {goal['deadline'][:10]} ({days_remaining} days remaining)")
                
                # Progress bar
                st.markdown(f"""
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {percentage}%">
                            {percentage:.1f}%
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col_right:
                # Action buttons
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button(f"Add R$ 100", key=f"add_{goal['id']}"):
                        engine.update_goal_progress(goal['id'], 100)
                        st.success("Progress updated!")
                        st.rerun()
                
                with col_btn2:
                    if st.button(f"Delete", key=f"del_{goal['id']}"):
                        delete_goal(goal['id'])
                        st.success("Goal deleted!")
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No goals yet. Create your first goal above!")

# Projections with goals
st.markdown("---")
st.subheader("📈 Projections with Goals")

projection_months = st.slider("Projection Period (months)", 3, 12, 6)
projections = engine.project_with_goals(months=projection_months)

if projections['goal_monthly_contribution'] > 0:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Base Monthly Net", f"R$ {projections['base_monthly_net']:.2f}")
    
    with col2:
        st.metric("Goal Contributions", f"R$ {projections['goal_monthly_contribution']:.2f}")
    
    with col3:
        st.metric("Adjusted Monthly Net", f"R$ {projections['adjusted_monthly_net']:.2f}")
    
    st.markdown("### Projected Balance with Goal Contributions")
    
    for proj in projections['projections']:
        st.markdown(
            f"**Month {proj['month']}**: R$ {proj['projected_balance']:.2f} "
            f"(after R$ {proj['goal_contribution']:.2f} contribution)"
        )
else:
    st.info("Set monthly targets for your goals to see projections.")
