import streamlit as st
from core.ai_layer import AILayer
from core.engine import FinanceEngine
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="FinOS",
    page_icon="💰",
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

st.title("Insights Financeiros IA")
st.markdown("---")

# Generate comprehensive insights
with st.spinner("Analisando seus dados financeiros..."):
    insights = ai_layer.generate_comprehensive_insights()

# Summary section
st.subheader("Resumo de Saude Financeira")

summary = insights['summary']

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total de Recomendacoes", summary['total_recommendations'])

with col2:
    st.metric("Alta Prioridade", summary['high_priority_count'])

with col3:
    status_color = "#9ABF17" if summary['health_status'] == 'Excellent' else "#D4DB7A" if summary['health_status'] == 'Needs Attention' else "#FF6B6B"
    st.markdown(f"""
        <div style="text-align: center; padding: 10px; background-color: #AED9C5; border-radius: 8px;">
            <small style="color: #282900;">Status de Saude</small><br>
            <span style="color: {status_color}; font-size: 24px; font-weight: 600;">{summary['health_status']}</span>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Spending Patterns
st.subheader("Analise de Padroes de Gastos")

patterns = insights['spending_patterns']

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Categorias de Maiores Gastos (Ultimos 90 Dias)")
    if patterns['top_categories']:
        for category, amount in patterns['top_categories']:
            monthly_avg = patterns['monthly_averages'].get(category, 0)
            st.markdown(f"**{category}**: R$ {amount:.2f} (R$ {monthly_avg:.2f}/month)")
    else:
        st.info("Nenhum dado de gasto disponivel")

with col2:
    st.markdown("### Frequencia de Gastos")
    if patterns['category_frequency']:
        for category, freq in sorted(patterns['category_frequency'].items(), key=lambda x: x[1], reverse=True)[:5]:
            st.markdown(f"**{category}**: {freq} transacoes")
    else:
        st.info("Nenhum dado de frequencia disponivel")

st.markdown("---")

# Anomalies Detection
st.subheader("Anomalias de Gastos")

anomalies = insights['anomalies']

if anomalies:
    for anomaly in anomalies:
        st.markdown(f'<div class="insight-card priority-high">', unsafe_allow_html=True)
        st.markdown(f"**{anomaly['category']}**: R$ {anomaly['amount']:.2f}")
        st.caption(f"{anomaly['description'] or 'Sem descricao'} | {anomaly['date'][:10]}")
        st.warning(f"Gasto incomum detectado ({anomaly['deviation']:.1f}x desvio da media)")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.success("Nenhum padrao de gasto incomum detectado!")

st.markdown("---")

# Savings Recommendations
st.subheader("Recomendacoes de Economia")

savings_recs = insights['savings_recommendations']

if savings_recs:
    for rec in savings_recs:
        priority_class = f"priority-{rec.get('priority', 'medium')}"
        st.markdown(f'<div class="insight-card {priority_class}">', unsafe_allow_html=True)
        st.markdown(f"**{rec['category']}**" if 'category' in rec else "**Economia**")
        st.markdown(rec['message'])
        if 'potential_savings' in rec:
            st.info(f"Economia potencial: R$ {rec['potential_savings']:.2f}/mes")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.success("Nenhuma recomendacao de economia especifica neste momento. Continue assim!")

st.markdown("---")

# Goal Recommendations
st.subheader("Recomendacoes de Metas")

goal_recs = insights['goal_recommendations']

if goal_recs:
    for rec in goal_recs:
        priority_class = f"priority-{rec.get('priority', 'medium')}"
        st.markdown(f'<div class="insight-card {priority_class}">', unsafe_allow_html=True)
        if 'goal' in rec:
            st.markdown(f"**{rec['goal']}**")
        st.markdown(rec['message'])
        if 'remaining' in rec:
            st.warning(f"Restante: R$ {rec['remaining']:.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.success("Suas metas estao no caminho certo!")

st.markdown("---")

# Debt Recommendations
st.subheader("Recomendacoes de Gerenciamento de Dividas")

debt_recs = insights['debt_recommendations']

if debt_recs:
    for rec in debt_recs:
        priority_class = f"priority-{rec.get('priority', 'medium')}"
        st.markdown(f'<div class="insight-card {priority_class}">', unsafe_allow_html=True)
        st.markdown(rec['message'])
        if 'interest_rate' in rec:
            st.warning(f"Taxa de juros: {rec['interest_rate']}%")
        if 'ratio' in rec:
            st.warning(f"Razao divida-renda: {rec['ratio'] * 100:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.success("Nenhuma preocupacao com dividas detectada!")

st.markdown("---")

# Investment Recommendations
st.subheader("Recomendacoes de Investimentos")

investment_recs = insights['investment_recommendations']

if investment_recs:
    for rec in investment_recs:
        priority_class = f"priority-{rec.get('priority', 'medium')}"
        st.markdown(f'<div class="insight-card {priority_class}">', unsafe_allow_html=True)
        st.markdown(rec['message'])
        if 'performance' in rec:
            st.warning(f"Desempenho atual: {rec['performance']:.1f}%")
        if 'asset_types' in rec:
            st.info(f"Tipos de ativos atuais: {', '.join(rec['asset_types'])}")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.success("Sua carteira de investimentos parece saudavel!")

st.markdown("---")

# Action Plan
st.subheader("Plano de Acao")

all_recommendations = (
    savings_recs + goal_recs + debt_recs + investment_recs
)

if all_recommendations:
    high_priority = [r for r in all_recommendations if r.get('priority') == 'high']
    medium_priority = [r for r in all_recommendations if r.get('priority') == 'medium']
    low_priority = [r for r in all_recommendations if r.get('priority') == 'low']
    
    if high_priority:
        st.markdown("### Acoes de Alta Prioridade")
        for i, rec in enumerate(high_priority, 1):
            st.markdown(f"{i}. {rec['message']}")
    
    if medium_priority:
        st.markdown("### Acoes de Media Prioridade")
        for i, rec in enumerate(medium_priority, 1):
            st.markdown(f"{i}. {rec['message']}")
    
    if low_priority:
        st.markdown("### Acoes de Baixa Prioridade")
        for i, rec in enumerate(low_priority, 1):
            st.markdown(f"{i}. {rec['message']}")
else:
    st.success("Nenhuma acao necessaria. Sua saude financeira e excelente!")

st.markdown("---")
st.caption(f"Insights gerados em {insights['generated_at'][:19]}")

st.markdown("---")
st.caption(f"Pagina de insights atualizada em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
