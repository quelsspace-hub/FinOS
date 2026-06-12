import streamlit as st
from core.database import (
    get_debts, create_debt, update_debt, delete_debt, 
    make_debt_payment, get_total_debt
)
from core.engine import FinanceEngine
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="FinOS",
    page_icon="�",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .debt-card {
        background-color: #AED9C5;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    
    .debt-paid {
        opacity: 0.6;
        background-color: #DDECF1;
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
    st.error("Por favor, selecione um usuario do dashboard principal primeiro.")
    st.stop()

user_id = st.session_state['user_id']

# Initialize engine
engine = FinanceEngine(st)
engine.set_user(user_id)

st.title("Gerenciamento de Dividas")
st.markdown("---")

# Create debt form
with st.expander("Adicionar Nova Divida", expanded=False):
    with st.form("debt_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_amount = st.number_input("Valor Total (R$)", min_value=0.01, step=100.0, value=1000.0)
        
        with col2:
            interest_rate = st.number_input("Taxa de Juros (% ao ano)", min_value=0.0, step=0.1, value=0.0)
        
        with col3:
            priority_rank = st.selectbox("Prioridade", [1, 2, 3], format_func=lambda x: {1: "Alta", 2: "Media", 3: "Baixa"}[x])
        
        col4 = st.columns(1)[0]
        with col4:
            due_date = st.date_input("Data de Vencimento (opcional)")
        
        submitted = st.form_submit_button("Adicionar Divida")
        
        if submitted and total_amount:
            due_date_str = due_date.isoformat() if due_date else None
            create_debt(
                user_id=user_id,
                total_amount=total_amount,
                interest_rate=interest_rate,
                priority_rank=priority_rank,
                due_date=due_date_str
            )
            st.success("Divida adicionada!")
            st.rerun()

# Display debts
st.subheader("Suas Dividas")

debts = get_debts(user_id)

if debts:
    # Total debt summary
    total_debt = get_total_debt(user_id)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Divida Original Total", f"R$ {total_debt['total_original']:.2f}")
    
    with col2:
        st.metric("Total Restante", f"R$ {total_debt['total_remaining']:.2f}")
    
    with col3:
        st.metric("Total Pago", f"R$ {total_debt['total_paid']:.2f}")
    
    st.markdown("---")
    
    # Snowball payoff plan
    snowball_plan = engine.calculate_debt_snowball()
    
    if snowball_plan:
        st.subheader("Plano de Pagamento Bola de Neve")
        st.info("Dividas ordenadas pelo menor saldo primeiro (Metodo Bola de Neve)")
        
        for plan in snowball_plan:
            st.markdown(
                f"**#{plan['payoff_order']}**: R$ {plan['remaining_amount']:.2f} restante "
                f"({plan['percentage_paid']:.1f}% pago)"
            )
        
        st.markdown("---")
    
    # Individual debt cards
    for debt in debts:
        with st.container():
            paid_class = "debt-paid" if debt['remaining_amount'] <= 0 else ""
            
            st.markdown(f'<div class="debt-card {paid_class}">', unsafe_allow_html=True)
            
            col_left, col_right = st.columns([3, 1])
            
            with col_left:
                priority_label = {1: "Alta", 2: "Media", 3: "Baixa"}[debt['priority_rank']]
                
                st.markdown(f"### Divida ID: {debt['id']}")
                st.caption(f"Prioridade: {priority_label} | Taxa de Juros: {debt['interest_rate']}% ao ano")
                
                if debt['due_date']:
                    due = datetime.fromisoformat(debt['due_date'])
                    days_remaining = (due - datetime.now()).days
                    st.caption(f"Vencimento: {debt['due_date'][:10]} ({days_remaining} dias restantes)")
                
                # Progress
                total = debt['total_amount']
                remaining = debt['remaining_amount']
                paid = total - remaining
                percentage = (paid / total) * 100 if total > 0 else 0
                
                st.caption(f"Total: R$ {total:.2f} | Pago: R$ {paid:.2f} | Restante: R$ {remaining:.2f}")
                
                # Progress bar
                st.markdown(f"""
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {percentage}%">
                            {percentage:.1f}%
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col_right:
                if debt['remaining_amount'] > 0:
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        payment_amount = st.number_input(
                            "Pagamento (R$)", 
                            min_value=0.01, 
                            max_value=debt['remaining_amount'], 
                            step=50.0, 
                            value=100.0,
                            key=f"pay_{debt['id']}"
                        )
                        if st.button("Pagar", key=f"pay_btn_{debt['id']}"):
                            make_debt_payment(debt['id'], payment_amount)
                            st.success("Pagamento registrado!")
                            st.rerun()
                    
                    with col_btn2:
                        if st.button("Excluir", key=f"del_{debt['id']}"):
                            delete_debt(debt['id'])
                            st.success("Divida excluida!")
                            st.rerun()
                else:
                    st.success("Pago!")
                    if st.button("Excluir", key=f"del_paid_{debt['id']}"):
                        delete_debt(debt['id'])
                        st.success("Divida excluida!")
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Nenhuma divida registrada. Otimo trabalho!")

# Payoff simulation
st.markdown("---")
st.subheader("Simulacao de Pagamento")

if debts:
    monthly_payment = st.number_input(
        "Pagamento Mensal para Quitacao de Dividas (R$)", 
        min_value=50.0, 
        step=50.0, 
        value=500.0
    )
    
    if st.button("Calcular Cronograma de Pagamento"):
        timeline = engine.calculate_debt_payoff_timeline(monthly_payment)
        
        if timeline['total_months'] > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Meses para Quitacao", timeline['total_months'])
            
            with col2:
                st.metric("Juros Total", f"R$ {timeline['total_interest_paid']:.2f}")
            
            st.markdown("### Cronograma de Pagamento")
            
            # Show first 12 months or all if less
            display_schedule = timeline['payoff_schedule'][:12]
            
            for entry in display_schedule:
                st.markdown(
                    f"**Mes {entry['month']}**: Pagamento R$ {entry['payment']:.2f} "
                    f"| Juros R$ {entry['interest']:.2f} | Principal R$ {entry['principal']:.2f} "
                    f"| Remaining R$ {entry['remaining']:.2f}"
                )
            
            if len(timeline['payoff_schedule']) > 12:
                st.info(f"... e mais {len(timeline['payoff_schedule']) - 12} meses")
        else:
            st.success("Todas as dividas estao pagas!")
else:
    st.info("Adicione dividas para ver a simulacao de pagamento.")

st.markdown("---")
st.caption(f"Pagina de dividas atualizada em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
