import streamlit as st
from core.database import (
    get_investments, create_investment, update_investment, 
    delete_investment, update_investment_performance, get_total_investments
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

st.title("Carteira de Investimentos")
st.markdown("---")

# Create investment form
with st.expander("Adicionar Investimento", expanded=False):
    with st.form("investment_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            asset_type = st.selectbox(
                "Tipo de Ativo",
                ["Acoes", "Titulos", "Imoveis", "Cripto", "ETF", "Fundos Mutuos", "Renda Fixa", "Outros"]
            )
        
        with col2:
            amount = st.number_input("Valor Investido (R$)", min_value=0.01, step=100.0, value=1000.0)
        
        with col3:
            performance = st.number_input("Desempenho (% ao ano)", min_value=-100.0, max_value=1000.0, step=0.1, value=0.0)
        
        submitted = st.form_submit_button("Adicionar Investimento")
        
        if submitted and amount:
            create_investment(
                user_id=user_id,
                asset_type=asset_type,
                amount=amount,
                performance=performance
            )
            st.success("Investimento adicionado!")
            st.rerun()

# Display investments
st.subheader("Seus Investimentos")

investments = get_investments(user_id)

if investments:
    # Total investment summary
    total_inv = get_total_investments(user_id)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Investido", f"R$ {total_inv['total_amount']:.2f}")
    
    with col2:
        st.metric("Valor Atual", f"R$ {total_inv['total_value']:.2f}")
    
    with col3:
        gain_class = "performance-positive" if total_inv['total_gain'] >= 0 else "performance-negative"
        st.markdown(f'<div class="{gain_class}">', unsafe_allow_html=True)
        st.metric("Ganho/Perda Total", f"R$ {total_inv['total_gain']:.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        perf_class = "performance-positive" if total_inv['average_performance'] >= 0 else "performance-negative"
        st.markdown(f'<div class="{perf_class}">', unsafe_allow_html=True)
        st.metric("Desempenho Medio", f"{total_inv['average_performance']:.2f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Investment allocation
    allocation = engine.calculate_investment_allocation()
    
    if allocation:
        st.subheader("Alocacao da Carteira")
        
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
                
                st.caption(f"Investido: R$ {inv['amount']:.2f} | Atual: R$ {current_value:.2f}")
                st.markdown(
                    f'<span class="{gain_class}">Ganho/Perda: R$ {gain:.2f}</span> | '
                    f'<span class="{perf_class}">Desempenho: {inv['performance']:.2f}%</span>',
                    unsafe_allow_html=True
                )
                
                if inv['purchase_date']:
                    purchase = datetime.fromisoformat(inv['purchase_date'])
                    days_held = (datetime.now() - purchase).days
                    st.caption(f"Comprado: {inv['purchase_date'][:10]} ({days_held} dias mantidos)")
            
            with col_right:
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    new_performance = st.number_input(
                        "Atualizar Desempenho (%)",
                        min_value=-100.0,
                        max_value=1000.0,
                        step=0.1,
                        value=inv['performance'],
                        key=f"perf_{inv['id']}"
                    )
                    if st.button("Atualizar", key=f"update_{inv['id']}"):
                        update_investment_performance(inv['id'], new_performance)
                        st.success("Desempenho atualizado!")
                        st.rerun()
                
                with col_btn2:
                    if st.button("Excluir", key=f"del_{inv['id']}"):
                        delete_investment(inv['id'])
                        st.success("Investimento excluido!")
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Nenhum investimento ainda. Comece a construir sua carteira acima!")

# Return projections
st.markdown("---")
st.subheader("Projeções de Retorno")

if investments:
    projection_months = st.slider("Periodo de Projeção (meses)", 3, 60, 12)
    returns = engine.calculate_investment_returns(projection_months)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Investido", f"R$ {returns['total_invested']:.2f}")
    
    with col2:
        st.metric("Valor Projetado", f"R$ {returns['total_value']:.2f}")
    
    with col3:
        gain_class = "performance-positive" if returns['total_gain'] >= 0 else "performance-negative"
        st.markdown(f'<div class="{gain_class}">', unsafe_allow_html=True)
        st.metric("Ganho Projetado", f"R$ {returns['total_gain']:.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### Projeções Mensais")
    
    # Show first 12 months or all if less
    display_projections = returns['projections'][:12]
    
    for proj in display_projections:
        st.markdown(
            f"**Mes {proj['month']}**: R$ {proj['value']:.2f} "
            f"(Ganho: R$ {proj['gain']:.2f}, Mensal: R$ {proj['monthly_gain']:.2f})"
        )
    
    if len(returns['projections']) > 12:
        st.info(f"... e mais {len(returns['projections']) - 12} meses")
else:
    st.info("Adicione investimentos para ver as projeções de retorno.")

# Net worth projection
st.markdown("---")
st.subheader("Projeção de Patrimonio Liquido (Dinheiro + Investimentos)")

if investments:
    net_worth = engine.project_with_investments(projection_months)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Dinheiro Atual", f"R$ {net_worth['current_cash_balance']:.2f}")
    
    with col2:
        st.metric("Investimentos Atuais", f"R$ {net_worth['current_investment_value']:.2f}")
    
    with col3:
        st.metric("Patrimonio Liquido Atual", f"R$ {net_worth['current_net_worth']:.2f}")
    
    st.markdown("### Projeções de Patrimonio Liquido")
    
    for proj in net_worth['projections'][:12]:
        st.markdown(
            f"**Mes {proj['month']}**: Dinheiro R$ {proj['cash_balance']:.2f} | "
            f"Investimentos R$ {proj['investment_value']:.2f} | "
            f"Patrimonio Liquido R$ {proj['total_net_worth']:.2f}"
        )
else:
    st.info("Adicione investimentos para ver as projeções de patrimonio liquido.")

st.markdown("---")
st.caption(f"Pagina de investimentos atualizada em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
