import streamlit as st
from core.reports import ReportGenerator
from core.engine import FinanceEngine
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Reports - FinOS",
    page_icon="📄",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .report-card {
        background-color: #AED9C5;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Get user from session state
if 'user_id' not in st.session_state:
    st.error("Please select a user from the main dashboard first.")
    st.stop()

user_id = st.session_state['user_id']

# Initialize Report Generator
report_gen = ReportGenerator(st)
report_gen.set_user(user_id)

st.title("📄 Financial Reports")
st.markdown("---")

# Date range selector
st.subheader("📅 Select Date Range")

col1, col2, col3 = st.columns(3)

with col1:
    start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))

with col2:
    end_date = st.date_input("End Date", value=datetime.now())

with col3:
    period_days = st.selectbox("Quick Select", [7, 30, 90, 180, 365], format_func=lambda x: f"{x} days")

if st.button("Apply Quick Select"):
    end_date = datetime.now()
    start_date = datetime.now() - timedelta(days=period_days)
    st.rerun()

st.markdown("---")

# Transaction Reports
st.subheader("💰 Transaction Reports")

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.markdown("### Export Transactions to CSV")
    st.caption("Download all transactions in CSV format")
    
    start_str = start_date.isoformat()
    end_str = end_date.isoformat()
    
    csv_data = report_gen.export_transactions_to_csv(start_str, end_str)
    st.download_button(
        label="Download CSV",
        data=csv_data,
        file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.markdown("### Export Transactions to Excel")
    st.caption("Download all transactions in Excel format")
    
    excel_data = report_gen.export_transactions_to_excel(start_str, end_str)
    st.download_button(
        label="Download Excel",
        data=excel_data,
        file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Summary Report
st.subheader("📊 Summary Report")

summary_days = st.slider("Summary Period (days)", 7, 365, 30)

summary = report_gen.generate_summary_report(summary_days)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Income", f"R$ {summary['balance']['total_income']:.2f}")

with col2:
    st.metric("Total Expenses", f"R$ {summary['balance']['total_expense']:.2f}")

with col3:
    st.metric("Net Flow", f"R$ {summary['summary']['net_flow']:.2f}")

with col4:
    st.metric("Health Score", f"{summary['health_score']['score']}")

st.markdown("### Download Summary Report")

summary_csv = report_gen.export_summary_to_csv(summary_days)
st.download_button(
    label="Download Summary CSV",
    data=summary_csv,
    file_name=f"summary_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

st.markdown("---")

# Goals Report
st.subheader("🎯 Goals Report")

goals_csv = report_gen.export_goals_to_csv()

st.download_button(
    label="Download Goals CSV",
    data=goals_csv,
    file_name=f"goals_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

st.markdown("---")

# Debts Report
st.subheader("💳 Debts Report")

debts_csv = report_gen.export_debts_to_csv()

st.download_button(
    label="Download Debts CSV",
    data=debts_csv,
    file_name=f"debts_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

st.markdown("---")

# Investments Report
st.subheader("📈 Investments Report")

investments_csv = report_gen.export_investments_to_csv()

st.download_button(
    label="Download Investments CSV",
    data=investments_csv,
    file_name=f"investments_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

st.markdown("---")

# Budget Report
st.subheader("📋 Budget Report")

budget_csv = report_gen.export_budget_to_csv()

st.download_button(
    label="Download Budget CSV",
    data=budget_csv,
    file_name=f"budget_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

st.markdown("---")

# Comprehensive Report
st.subheader("📑 Comprehensive Report")

st.info("This report includes all financial data in JSON format for advanced analysis.")

if st.button("Generate Comprehensive Report"):
    with st.spinner("Generating comprehensive report..."):
        comprehensive = report_gen.generate_comprehensive_report(summary_days)
        
        import json
        json_data = json.dumps(comprehensive, indent=2, default=str)
        
        st.download_button(
            label="Download Comprehensive JSON",
            data=json_data,
            file_name=f"comprehensive_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

st.markdown("---")

# Report Preview
st.subheader("👁️ Report Preview")

preview_option = st.selectbox(
    "Select Report to Preview",
    ["Summary", "Transactions", "Goals", "Debts", "Investments", "Budget"]
)

if preview_option == "Summary":
    st.json(summary)
elif preview_option == "Transactions":
    transactions = report_gen.db.get_transactions(user_id, limit=100)
    st.dataframe(transactions)
elif preview_option == "Goals":
    goals = report_gen.db.get_goals(user_id)
    st.dataframe(goals)
elif preview_option == "Debts":
    debts = report_gen.db.get_debts(user_id)
    st.dataframe(debts)
elif preview_option == "Investments":
    investments = report_gen.db.get_investments(user_id)
    st.dataframe(investments)
elif preview_option == "Budget":
    budgets = report_gen.db.get_budgets(user_id)
    st.dataframe(budgets)

st.markdown("---")
st.caption(f"Reports generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
