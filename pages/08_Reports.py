import streamlit as st
from core.reports import ReportGenerator
from core.engine import FinanceEngine
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="FinOS",
    page_icon="�",
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
    st.error("Por favor, selecione um usuario do dashboard principal primeiro.")
    st.stop()

user_id = st.session_state['user_id']

# Initialize Report Generator
report_gen = ReportGenerator(st)
report_gen.set_user(user_id)

st.title("Relatorios Financeiros")
st.markdown("---")

# Date range selector
st.subheader("Selecionar Periodo")

col1, col2, col3 = st.columns(3)

with col1:
    start_date = st.date_input("Data de Inicio", value=datetime.now() - timedelta(days=30))

with col2:
    end_date = st.date_input("Data de Fim", value=datetime.now())

with col3:
    period_days = st.selectbox("Selecao Rapida", [7, 30, 90, 180, 365], format_func=lambda x: f"{x} dias")

if st.button("Aplicar Selecao Rapida"):
    end_date = datetime.now()
    start_date = datetime.now() - timedelta(days=period_days)
    st.rerun()

st.markdown("---")

# Transaction Reports
st.subheader("Relatorios de Transacoes")

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.markdown("### Exportar Transacoes para CSV")
    st.caption("Baixar todas as transacoes em formato CSV")
    
    start_str = start_date.isoformat()
    end_str = end_date.isoformat()
    
    csv_data = report_gen.export_transactions_to_csv(start_str, end_str)
    st.download_button(
        label="Baixar CSV",
        data=csv_data,
        file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.markdown("### Exportar Transacoes para Excel")
    st.caption("Baixar todas as transacoes em formato Excel")
    
    excel_data = report_gen.export_transactions_to_excel(start_str, end_str)
    st.download_button(
        label="Baixar Excel",
        data=excel_data,
        file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Summary Report
st.subheader("Relatorio Resumido")

summary_days = st.slider("Periodo do Resumo (dias)", 7, 365, 30)

summary = report_gen.generate_summary_report(summary_days)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Receita Total", f"R$ {summary['balance']['total_income']:.2f}")

with col2:
    st.metric("Despesas Totais", f"R$ {summary['balance']['total_expense']:.2f}")

with col3:
    st.metric("Fluxo Liquido", f"R$ {summary['summary']['net_flow']:.2f}")

with col4:
    st.metric("Pontuacao de Saude", f"{summary['health_score']['score']}")

st.markdown("### Baixar Relatorio Resumido")

summary_csv = report_gen.export_summary_to_csv(summary_days)
st.download_button(
    label="Baixar Resumo CSV",
    data=summary_csv,
    file_name=f"summary_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

st.markdown("---")

# Goals Report
st.subheader("Relatorio de Metas")

goals_csv = report_gen.export_goals_to_csv()

st.download_button(
    label="Baixar Metas CSV",
    data=goals_csv,
    file_name=f"goals_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

st.markdown("---")

# Debts Report
st.subheader("Relatorio de Dividas")

debts_csv = report_gen.export_debts_to_csv()

st.download_button(
    label="Baixar Dividas CSV",
    data=debts_csv,
    file_name=f"debts_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

st.markdown("---")

# Investments Report
st.subheader("Relatorio de Investimentos")

investments_csv = report_gen.export_investments_to_csv()

st.download_button(
    label="Baixar Investimentos CSV",
    data=investments_csv,
    file_name=f"investments_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

st.markdown("---")

# Budget Report
st.subheader("Relatorio de Orcamento")

budget_csv = report_gen.export_budget_to_csv()

st.download_button(
    label="Baixar Orcamento CSV",
    data=budget_csv,
    file_name=f"budget_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

st.markdown("---")

# Comprehensive Report
st.subheader("Relatorio Completo")

st.info("Este relatorio inclui todos os dados financeiros em formato JSON para analise avancada.")

if st.button("Gerar Relatorio Completo"):
    with st.spinner("Gerando relatorio completo..."):
        comprehensive = report_gen.generate_comprehensive_report(summary_days)
        
        import json
        json_data = json.dumps(comprehensive, indent=2, default=str)
        
        st.download_button(
            label="Baixar JSON Completo",
            data=json_data,
            file_name=f"comprehensive_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

st.markdown("---")

# Report Preview
st.subheader("Previsualizacao do Relatorio")

preview_option = st.selectbox(
    "Selecionar Relatorio para Previsualizar",
    ["Resumo", "Transacoes", "Metas", "Dividas", "Investimentos", "Orcamento"]
)

if preview_option == "Resumo":
    st.json(summary)
elif preview_option == "Transacoes":
    transactions = report_gen.db.get_transactions(user_id, limit=100)
    st.dataframe(transactions)
elif preview_option == "Metas":
    goals = report_gen.db.get_goals(user_id)
    st.dataframe(goals)
elif preview_option == "Dividas":
    debts = report_gen.db.get_debts(user_id)
    st.dataframe(debts)
elif preview_option == "Investimentos":
    investments = report_gen.db.get_investments(user_id)
    st.dataframe(investments)
elif preview_option == "Orcamento":
    budgets = report_gen.db.get_budgets(user_id)
    st.dataframe(budgets)

st.markdown("---")
st.caption(f"Relatorios gerados em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.markdown("---")
st.caption(f"Pagina de relatorios atualizada em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
