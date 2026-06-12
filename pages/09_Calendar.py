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
    page_title="FinOS",
    page_icon="�",
    layout="wide"
)

# Get user from session state
if 'user_id' not in st.session_state:
    st.error("Por favor, selecione um usuario do dashboard principal primeiro.")
    st.stop()

user_id = st.session_state['user_id']

st.title("Calendario de Pagamentos")
st.markdown("---")

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["Calendario de Pagamentos", "Transacoes Recorrentes", "Gerar Transacoes"])

# Tab 1: Payment Calendar
with tab1:
    st.subheader("Cronograma de Pagamentos")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Data de Inicio", value=datetime.now().replace(day=1))
    with col2:
        end_date = st.date_input("Data de Fim", value=datetime.now() + timedelta(days=30))
    
    # Add new payment
    with st.expander("Adicionar Novo Pagamento", expanded=False):
        with st.form("payment_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                name = st.text_input("Nome do Pagamento")
                amount = st.number_input("Valor (R$)", min_value=0.01, step=0.01, value=100.0)
            
            with col2:
                category = st.selectbox(
                    "Categoria",
                    ["Aluguel", "Utilidades", "Internet", "Telefone", "Seguro", "Assinatura", "Emprestimo", "Cartao de Credito", "Outros"]
                )
                due_date = st.date_input("Data de Vencimento")
            
            with col3:
                is_recurring = st.checkbox("Pagamento Recorrente")
                notes = st.text_area("Notas (opcional)")
            
            submitted = st.form_submit_button("Adicionar Pagamento")
            
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
                st.success("Pagamento adicionado!")
                st.rerun()
    
    # Display payments
    payments = get_payments(user_id, start_date.isoformat(), end_date.isoformat())
    
    if payments:
        st.markdown(f"### Pagamentos ({len(payments)})")
        
        for payment in payments:
            with st.container():
                due = datetime.fromisoformat(payment['due_date'])
                days_remaining = (due - datetime.now()).days
                is_overdue = days_remaining < 0
                
                col_left, col_right = st.columns([4, 1])
                
                with col_left:
                    status_text = "ATRASADO" if is_overdue and not payment['is_paid'] else "PAGO" if payment['is_paid'] else "PENDENTE"
                    st.markdown(f"### {status_text} {payment['name']}")
                    st.caption(f"Vencimento: {payment['due_date'][:10]} ({days_remaining} dias restantes)")
                    st.markdown(f"**Valor**: R$ {payment['amount']:.2f} | **Categoria**: {payment['category'] or 'N/A'}")
                    
                    if payment['is_paid']:
                        st.success(f"Pago em {payment['paid_date'][:10] if payment['paid_date'] else 'N/A'}")
                    elif is_overdue:
                        st.error(f"ATRASADO por {abs(days_remaining)} dias")
                    else:
                        st.info(f"Vence em {days_remaining} dias")
                    
                    if payment['notes']:
                        st.caption(f"Notas: {payment['notes']}")
                
                with col_right:
                    if not payment['is_paid']:
                        if st.button("Marcar Pago", key=f"pay_{payment['id']}"):
                            mark_payment_paid(payment['id'])
                            st.success("Pagamento marcado como pago!")
                            st.rerun()
                    
                    if st.button("Excluir", key=f"del_{payment['id']}"):
                        delete_payment(payment['id'])
                        st.success("Pagamento excluido!")
                        st.rerun()
                
                st.markdown("---")
    else:
        st.info("Nenhum pagamento agendado para este periodo.")

# Tab 2: Recurring Transactions
with tab2:
    st.subheader("Transacoes Recorrentes")
    
    # Add new recurring transaction
    with st.expander("Adicionar Transacao Recorrente", expanded=False):
        with st.form("recurring_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                name = st.text_input("Nome da Transacao")
                amount = st.number_input("Valor (R$)", min_value=0.01, step=0.01, value=100.0)
            
            with col2:
                trans_type = st.selectbox("Tipo", ["receita", "despesa"])
                category = st.selectbox(
                    "Categoria",
                    ["Salario", "Aluguel", "Utilidades", "Internet", "Telefone", "Seguro", "Assinatura", "Emprestimo", "Cartao de Credito", "Outros"]
                )
            
            with col3:
                frequency = st.selectbox(
                    "Frequencia",
                    ["diario", "semanal", "quinzenal", "mensal", "trimestral", "anual"]
                )
                start_date = st.date_input("Data de Inicio")
                end_date = st.date_input("Data de Fim (opcional)", value=None)
            
            submitted = st.form_submit_button("Adicionar Transacao Recorrente")
            
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
                st.success("Transacao recorrente adicionada!")
                st.rerun()
    
    # Display recurring transactions
    recurring = get_recurring_transactions(user_id)
    
    if recurring:
        st.markdown(f"### Transacoes Recorrentes Ativas ({len(recurring)})")
        
        for rec in recurring:
            with st.container():
                st.markdown(f"### {rec['name']}")
                st.caption(f"Frequencia: {rec['frequency']} | Tipo: {rec['type']} | Categoria: {rec['category']}")
                st.markdown(f"**Valor**: R$ {rec['amount']:.2f}")
                st.caption(f"Inicio: {rec['start_date'][:10]} | Fim: {rec['end_date'][:10] if rec['end_date'] else 'Continuo'}")
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button("Excluir", key=f"del_rec_{rec['id']}"):
                        delete_recurring_transaction(rec['id'])
                        st.success("Transacao recorrente excluida!")
                        st.rerun()
                
                with col_btn2:
                    if st.button("Desativar", key=f"deact_{rec['id']}"):
                        deactivate_recurring_transaction(rec['id'])
                        st.success("Transacao recorrente desativada!")
                        st.rerun()
                
                st.markdown("---")
    else:
        st.info("Nenhuma transacao recorrente configurada.")

# Tab 3: Generate Transactions
with tab3:
    st.subheader("Gerar Transacoes a partir de Padroes Recorrentes")
    
    st.info("Isso ira gerar transacoes reais a partir dos seus padroes de transacoes recorrentes ate uma data especificada.")
    
    target_date = st.date_input("Gerar transacoes ate", value=datetime.now() + timedelta(days=30))
    
    if st.button("Gerar Transacoes"):
        with st.spinner("Gerando transacoes..."):
            count = generate_recurring_transactions(user_id, target_date.isoformat())
            st.success(f"Geradas {count} transacoes!")
            st.rerun()

st.markdown("---")
st.caption(f"Calendario atualizado em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.markdown("---")
st.caption(f"Pagina de calendario atualizada em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
