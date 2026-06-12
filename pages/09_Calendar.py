import streamlit as st
from core.database import (
    create_payment, get_payments, update_payment, mark_payment_paid, delete_payment,
    create_recurring_transaction, get_recurring_transactions, 
    update_recurring_transaction, deactivate_recurring_transaction, delete_recurring_transaction,
    generate_recurring_transactions
)
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Payment Calendar - FinOS",
    page_icon="📅",
    layout="wide"
)

# Get user from session state
if 'user_id' not in st.session_state:
    st.error("Please select a user from the main dashboard first.")
    st.stop()

user_id = st.session_state['user_id']

st.title("📅 Payment Calendar")
st.markdown("---")

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["Payment Calendar", "Recurring Transactions", "Generate Transactions"])

# Tab 1: Payment Calendar
with tab1:
    st.subheader("📋 Payment Schedule")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now().replace(day=1))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now() + timedelta(days=30))
    
    # Add new payment
    with st.expander("➕ Add New Payment", expanded=False):
        with st.form("payment_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                name = st.text_input("Payment Name")
                amount = st.number_input("Amount (R$)", min_value=0.01, step=0.01, value=100.0)
            
            with col2:
                category = st.selectbox(
                    "Category",
                    ["Rent", "Utilities", "Internet", "Phone", "Insurance", "Subscription", "Loan", "Credit Card", "Other"]
                )
                due_date = st.date_input("Due Date")
            
            with col3:
                is_recurring = st.checkbox("Recurring Payment")
                notes = st.text_area("Notes (optional)")
            
            submitted = st.form_submit_button("Add Payment")
            
            if submitted and name and amount:
                create_payment(
                    user_id=user_id,
                    name=name,
                    amount=amount,
                    due_date=due_date.isoformat(),
                    category=category,
                    is_recurring=is_recurring,
                    notes=notes
                )
                st.success("Payment added!")
                st.rerun()
    
    # Display payments
    payments = get_payments(user_id, start_date.isoformat(), end_date.isoformat())
    
    if payments:
        st.markdown(f"### Payments ({len(payments)})")
        
        for payment in payments:
            with st.container():
                due = datetime.fromisoformat(payment['due_date'])
                days_remaining = (due - datetime.now()).days
                is_overdue = days_remaining < 0
                
                col_left, col_right = st.columns([4, 1])
                
                with col_left:
                    status_color = "🔴" if is_overdue and not payment['is_paid'] else "🟢" if payment['is_paid'] else "🟡"
                    st.markdown(f"### {status_color} {payment['name']}")
                    st.caption(f"Due: {payment['due_date'][:10]} ({days_remaining} days remaining)")
                    st.markdown(f"**Amount**: R$ {payment['amount']:.2f} | **Category**: {payment['category'] or 'N/A'}")
                    
                    if payment['is_paid']:
                        st.success(f"✅ Paid on {payment['paid_date'][:10] if payment['paid_date'] else 'N/A'}")
                    elif is_overdue:
                        st.error(f"⚠️ OVERDUE by {abs(days_remaining)} days")
                    else:
                        st.info(f"⏳ Due in {days_remaining} days")
                    
                    if payment['notes']:
                        st.caption(f"Notes: {payment['notes']}")
                
                with col_right:
                    if not payment['is_paid']:
                        if st.button("Mark Paid", key=f"pay_{payment['id']}"):
                            mark_payment_paid(payment['id'])
                            st.success("Payment marked as paid!")
                            st.rerun()
                    
                    if st.button("🗑️ Delete", key=f"del_{payment['id']}"):
                        delete_payment(payment['id'])
                        st.success("Payment deleted!")
                        st.rerun()
                
                st.markdown("---")
    else:
        st.info("No payments scheduled for this period.")

# Tab 2: Recurring Transactions
with tab2:
    st.subheader("🔄 Recurring Transactions")
    
    # Add new recurring transaction
    with st.expander("➕ Add Recurring Transaction", expanded=False):
        with st.form("recurring_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                name = st.text_input("Transaction Name")
                amount = st.number_input("Amount (R$)", min_value=0.01, step=0.01, value=100.0)
            
            with col2:
                trans_type = st.selectbox("Type", ["income", "expense"])
                category = st.selectbox(
                    "Category",
                    ["Salary", "Rent", "Utilities", "Internet", "Phone", "Insurance", "Subscription", "Loan", "Credit Card", "Other"]
                )
            
            with col3:
                frequency = st.selectbox(
                    "Frequency",
                    ["daily", "weekly", "biweekly", "monthly", "quarterly", "yearly"]
                )
                start_date = st.date_input("Start Date")
                end_date = st.date_input("End Date (optional)", value=None)
            
            submitted = st.form_submit_button("Add Recurring Transaction")
            
            if submitted and name and amount:
                end_date_str = end_date.isoformat() if end_date else None
                create_recurring_transaction(
                    user_id=user_id,
                    name=name,
                    amount=amount,
                    category=category,
                    trans_type=trans_type,
                    frequency=frequency,
                    start_date=start_date.isoformat(),
                    end_date=end_date_str
                )
                st.success("Recurring transaction added!")
                st.rerun()
    
    # Display recurring transactions
    recurring = get_recurring_transactions(user_id)
    
    if recurring:
        st.markdown(f"### Active Recurring Transactions ({len(recurring)})")
        
        for rec in recurring:
            with st.container():
                st.markdown(f"### {rec['name']}")
                st.caption(f"Frequency: {rec['frequency']} | Type: {rec['type']} | Category: {rec['category']}")
                st.markdown(f"**Amount**: R$ {rec['amount']:.2f}")
                st.caption(f"Start: {rec['start_date'][:10]} | End: {rec['end_date'][:10] if rec['end_date'] else 'Ongoing'}")
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button("🗑️ Delete", key=f"del_rec_{rec['id']}"):
                        delete_recurring_transaction(rec['id'])
                        st.success("Recurring transaction deleted!")
                        st.rerun()
                
                with col_btn2:
                    if st.button("⏸️ Deactivate", key=f"deact_{rec['id']}"):
                        deactivate_recurring_transaction(rec['id'])
                        st.success("Recurring transaction deactivated!")
                        st.rerun()
                
                st.markdown("---")
    else:
        st.info("No recurring transactions set up.")

# Tab 3: Generate Transactions
with tab3:
    st.subheader("⚡ Generate Transactions from Recurring Patterns")
    
    st.info("This will generate actual transactions from your recurring transaction patterns up to a specified date.")
    
    target_date = st.date_input("Generate transactions up to", value=datetime.now() + timedelta(days=30))
    
    if st.button("Generate Transactions"):
        with st.spinner("Generating transactions..."):
            count = generate_recurring_transactions(user_id, target_date.isoformat())
            st.success(f"Generated {count} transactions!")
            st.rerun()

st.markdown("---")
st.caption(f"Calendar updated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
