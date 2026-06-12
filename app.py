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
    page_title="FinOS",
    page_icon="💰",
    layout="wide"
)

# Custom CSS
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

st.title("FinOS")
st.markdown("---")

# Navigation
st.sidebar.header("Navegacao")
st.sidebar.page_link("app.py", label="Dashboard")
st.sidebar.page_link("pages/01_Budget.py", label="Orcamento")
st.sidebar.page_link("pages/02_Goals.py", label="Metas")
st.sidebar.page_link("pages/03_Wishlist.py", label="Lista de Desejos")
st.sidebar.page_link("pages/04_Debts.py", label="Dividas")
st.sidebar.page_link("pages/05_Investments.py", label="Investimentos")
st.sidebar.page_link("pages/06_Insights.py", label="Insights IA")
st.sidebar.page_link("pages/07_Visualizations.py", label="Visualizacoes")
st.sidebar.page_link("pages/08_Reports.py", label="Relatorios")
st.sidebar.page_link("pages/09_Calendar.py", label="Calendario")
st.sidebar.markdown("---")

# User settings
if 'user_settings' not in st.session_state:
    st.session_state.user_settings = {
        'apelido': 'Usuario',
        'idade': 30,
        'renda_mensal': 5000.0
    }

st.sidebar.header("Configuracoes")
with st.sidebar.form("settings_form"):
    apelido = st.text_input("Apelido", value=st.session_state.user_settings['apelido'])
    idade = st.number_input("Idade", min_value=1, max_value=120, value=st.session_state.user_settings['idade'])
    renda_mensal = st.number_input("Renda Mensal (R$)", min_value=0.0, value=st.session_state.user_settings['renda_mensal'])
    submitted = st.form_submit_button("Salvar")
    if submitted:
        st.session_state.user_settings = {
            'apelido': apelido,
            'idade': idade,
            'renda_mensal': renda_mensal
        }
        st.sidebar.success("Configuracoes salvas!")

# Default user ID (simplified - no user system)
user_id = 1
st.session_state['user_id'] = user_id

# Initialize engine with default user
engine = FinanceEngine(st)
engine.set_user(user_id)

# Main dashboard
col1, col2, col3, col4 = st.columns(4)

# Calculate balance using engine
balance_data = engine.calculate_balance()

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Receita Total", f"R$ {balance_data['total_income']:.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Despesas Totais", f"R$ {balance_data['total_expense']:.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    balance_class = "balance-positive" if balance_data['balance'] >= 0 else "balance-negative"
    st.markdown(f'<div class="metric-card {balance_class}">', unsafe_allow_html=True)
    st.metric("Saldo Atual", f"R$ {balance_data['balance']:.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    # Financial health score
    health_score = engine.get_financial_health_score()
    score_color = "#9ABF17" if health_score['score'] >= 60 else "#D4DB7A"
    st.markdown(f"""
        <div class="metric-card" style="text-align: center;">
            <small style="color: #282900;">Saude Financeira</small><br>
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
    st.subheader("Metas, Lista de Desejos, Dividas e Investimentos")
    col_goals, col_wishlist, col_debts, col_investments = st.columns(4)
    
    with col_goals:
        if goals:
            total_goals = len(goals)
            completed_goals = len([g for g in goals if g['progress'] >= g['target_value']])
            st.metric("Progresso de Metas", f"{completed_goals}/{total_goals}")
        else:
            st.info("Nenhuma meta definida")
    
    with col_wishlist:
        if wishlist:
            total_wishlist = len(wishlist)
            achieved_items = len([w for w in wishlist if w['status'] == 'achieved'])
            st.metric("Lista de Desejos", f"{achieved_items}/{total_wishlist} alcançados")
        else:
            st.info("Lista de desejos vazia")
    
    with col_debts:
        if total_debt['total_remaining'] > 0:
            st.metric("Divida Total", f"R$ {total_debt['total_remaining']:.2f}")
        else:
            st.success("Sem dividas!")
    
    with col_investments:
        if total_investments['total_amount'] > 0:
            st.metric("Investimentos", f"R$ {total_investments['total_value']:.2f}")
        else:
            st.info("Sem investimentos")
    
    st.markdown("---")

# Budget alerts
budget_alerts = engine.check_budget_alerts()
if budget_alerts:
    st.subheader("Alertas de Orcamento")
    for alert in budget_alerts:
        st.error(
            f"**{alert['category']}**: Acima do orcamento em R$ {alert['over_budget']:.2f} "
            f"({alert['percentage_used']:.1f}% usado)"
        )
    st.markdown("---")

# AI Insights Quick Summary
from core.ai_layer import AILayer
ai_layer = AILayer(st)
ai_layer.set_user(user_id)

insights = ai_layer.generate_comprehensive_insights()

if insights['summary']['total_recommendations'] > 0:
    st.subheader("Resumo de Insights IA")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total de Recomendacoes", insights['summary']['total_recommendations'])
    
    with col2:
        st.metric("Alta Prioridade", insights['summary']['high_priority_count'])
    
    if insights['summary']['high_priority_count'] > 0:
        st.warning(f"{insights['summary']['high_priority_count']} recomendacoes de alta prioridade. Verifique a pagina de Insights IA para detalhes.")
    else:
        st.success("Sem problemas de alta prioridade!")
    
    st.markdown("---")

# ML Spending Prediction
st.subheader("Previsao de Gastos com ML")

prediction_months = st.selectbox("Periodo de Previsao (meses)", [1, 3, 6, 12], index=1)

if st.button("Gerar Previsao"):
    ml_prediction = engine.predict_spending_ml(prediction_months)
    
    if ml_prediction['total_predicted'] > 0:
        st.metric(f"Gasto Previsto ({prediction_months} meses)", f"R$ {ml_prediction['total_predicted']:.2f}")
        
        st.markdown("### Por Categoria")
        for category, amount in ml_prediction['by_category'].items():
            st.markdown(f"**{category}**: R$ {amount:.2f}")
    else:
        st.info("Dados insuficientes para previsao ML. Adicione mais transacoes para habilitar previsoes.")

st.markdown("---")

# Transaction form
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Adicionar Transacao")
    with st.form("transaction_form"):
        trans_type = st.selectbox("Tipo", ["renda", "despesa"])
        category = st.selectbox(
            "Categoria",
            ["Salario", "Alimentacao", "Transporte", "Moradia", "Entretenimento", 
             "Saude", "Educacao", "Compras", "Outros"]
        )
        amount = st.number_input("Valor (R$)", min_value=0.01, step=0.01, value=100.0)
        description = st.text_input("Descricao (opcional)")
        submitted = st.form_submit_button("Adicionar Transacao")
        
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
            
            st.success(f"Transacao adicionada! Categorizada como: {final_category}")
            st.rerun()

with col_right:
    st.subheader("Gastos por Categoria")
    category_spending = get_transactions_by_category(user_id)
    
    if category_spending:
        for category, amount in sorted(category_spending.items(), key=lambda x: x[1], reverse=True):
            st.markdown(f"**{category}**: R$ {amount:.2f}")
    else:
        st.info("Nenhuma despesa registrada ainda.")

st.markdown("---")

# Recent transactions
st.subheader("Transacoes Recentes")
transactions = get_transactions(user_id, limit=20)

if transactions:
    for trans in transactions:
        with st.container():
            col_type, col_cat, col_amt, col_date = st.columns([1, 2, 2, 2])
            
            color = "#9ABF17" if trans['type'] == 'income' else "#282900"
            
            col_type.markdown("↑" if trans['type'] == 'income' else "↓")
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
    st.info("Nenhuma transacao ainda. Adicione sua primeira transacao acima!")

# Footer
st.markdown("---")
st.write("Versão 1.1")
