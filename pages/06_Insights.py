import streamlit as st
from core.ai_layer import AILayer
from core.engine import FinanceEngine
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AI Insights - FinOS",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .insight-card {
        background-color: #AED9C5;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    
    .priority-high {
        border-left: 4px solid #D4DB7A;
    }
    
    .priority-medium {
        border-left: 4px solid #9ABF17;
    }
    
    .priority-low {
        border-left: 4px solid #84BF93;
    }
</style>
""", unsafe_allow_html=True)

# Get user from session state
if 'user_id' not in st.session_state:
    st.error("Please select a user from the main dashboard first.")
    st.stop()

user_id = st.session_state['user_id']

# Initialize AI Layer
ai_layer = AILayer(st)
ai_layer.set_user(user_id)

st.title("🤖 AI Financial Insights")
st.markdown("---")

# Generate comprehensive insights
with st.spinner("Analyzing your financial data..."):
    insights = ai_layer.generate_comprehensive_insights()

# Summary section
st.subheader("📊 Financial Health Summary")

summary = insights['summary']

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Recommendations", summary['total_recommendations'])

with col2:
    st.metric("High Priority", summary['high_priority_count'])

with col3:
    status_color = "#9ABF17" if summary['health_status'] == 'Excellent' else "#D4DB7A" if summary['health_status'] == 'Needs Attention' else "#FF6B6B"
    st.markdown(f"""
        <div style="text-align: center; padding: 10px; background-color: #AED9C5; border-radius: 8px;">
            <small style="color: #282900;">Health Status</small><br>
            <span style="color: {status_color}; font-size: 24px; font-weight: 600;">{summary['health_status']}</span>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Spending Patterns
st.subheader("💰 Spending Patterns Analysis")

patterns = insights['spending_patterns']

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Top Spending Categories (Last 90 Days)")
    if patterns['top_categories']:
        for category, amount in patterns['top_categories']:
            monthly_avg = patterns['monthly_averages'].get(category, 0)
            st.markdown(f"**{category}**: R$ {amount:.2f} (R$ {monthly_avg:.2f}/month)")
    else:
        st.info("No spending data available")

with col2:
    st.markdown("### Spending Frequency")
    if patterns['category_frequency']:
        for category, freq in sorted(patterns['category_frequency'].items(), key=lambda x: x[1], reverse=True)[:5]:
            st.markdown(f"**{category}**: {freq} transactions")
    else:
        st.info("No frequency data available")

st.markdown("---")

# Anomalies Detection
st.subheader("⚠️ Spending Anomalies")

anomalies = insights['anomalies']

if anomalies:
    for anomaly in anomalies:
        st.markdown(f'<div class="insight-card priority-high">', unsafe_allow_html=True)
        st.markdown(f"**{anomaly['category']}**: R$ {anomaly['amount']:.2f}")
        st.caption(f"{anomaly['description'] or 'No description'} | {anomaly['date'][:10]}")
        st.warning(f"Unusual spending detected ({anomaly['deviation']:.1f}x deviation from average)")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.success("No unusual spending patterns detected! ✅")

st.markdown("---")

# Savings Recommendations
st.subheader("💡 Savings Recommendations")

savings_recs = insights['savings_recommendations']

if savings_recs:
    for rec in savings_recs:
        priority_class = f"priority-{rec.get('priority', 'medium')}"
        st.markdown(f'<div class="insight-card {priority_class}">', unsafe_allow_html=True)
        st.markdown(f"**{rec['category']}**" if 'category' in rec else "**Savings**")
        st.markdown(rec['message'])
        if 'potential_savings' in rec:
            st.info(f"Potential savings: R$ {rec['potential_savings']:.2f}/month")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.success("No specific savings recommendations at this time. Keep up the good work! ✅")

st.markdown("---")

# Goal Recommendations
st.subheader("🎯 Goal Recommendations")

goal_recs = insights['goal_recommendations']

if goal_recs:
    for rec in goal_recs:
        priority_class = f"priority-{rec.get('priority', 'medium')}"
        st.markdown(f'<div class="insight-card {priority_class}">', unsafe_allow_html=True)
        if 'goal' in rec:
            st.markdown(f"**{rec['goal']}**")
        st.markdown(rec['message'])
        if 'remaining' in rec:
            st.warning(f"Remaining: R$ {rec['remaining']:.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.success("Your goals are on track! 🎉")

st.markdown("---")

# Debt Recommendations
st.subheader("💳 Debt Management Recommendations")

debt_recs = insights['debt_recommendations']

if debt_recs:
    for rec in debt_recs:
        priority_class = f"priority-{rec.get('priority', 'medium')}"
        st.markdown(f'<div class="insight-card {priority_class}">', unsafe_allow_html=True)
        st.markdown(rec['message'])
        if 'interest_rate' in rec:
            st.warning(f"Interest rate: {rec['interest_rate']}%")
        if 'ratio' in rec:
            st.warning(f"Debt-to-income ratio: {rec['ratio'] * 100:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.success("No debt concerns detected! 🎉")

st.markdown("---")

# Investment Recommendations
st.subheader("📈 Investment Recommendations")

investment_recs = insights['investment_recommendations']

if investment_recs:
    for rec in investment_recs:
        priority_class = f"priority-{rec.get('priority', 'medium')}"
        st.markdown(f'<div class="insight-card {priority_class}">', unsafe_allow_html=True)
        st.markdown(rec['message'])
        if 'performance' in rec:
            st.warning(f"Current performance: {rec['performance']:.1f}%")
        if 'asset_types' in rec:
            st.info(f"Current asset types: {', '.join(rec['asset_types'])}")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.success("Your investment portfolio looks healthy! 🎉")

st.markdown("---")

# Action Plan
st.subheader("📋 Action Plan")

all_recommendations = (
    savings_recs + goal_recs + debt_recs + investment_recs
)

if all_recommendations:
    high_priority = [r for r in all_recommendations if r.get('priority') == 'high']
    medium_priority = [r for r in all_recommendations if r.get('priority') == 'medium']
    low_priority = [r for r in all_recommendations if r.get('priority') == 'low']
    
    if high_priority:
        st.markdown("### 🔴 High Priority Actions")
        for i, rec in enumerate(high_priority, 1):
            st.markdown(f"{i}. {rec['message']}")
    
    if medium_priority:
        st.markdown("### 🟡 Medium Priority Actions")
        for i, rec in enumerate(medium_priority, 1):
            st.markdown(f"{i}. {rec['message']}")
    
    if low_priority:
        st.markdown("### 🟢 Low Priority Actions")
        for i, rec in enumerate(low_priority, 1):
            st.markdown(f"{i}. {rec['message']}")
else:
    st.success("No actions needed. Your financial health is excellent! 🎉")

st.markdown("---")
st.caption(f"Insights generated on {insights['generated_at'][:19]}")
