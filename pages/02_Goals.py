import streamlit as st
from core.database import (
    get_goals, create_goal, update_goal, delete_goal, get_balance
)
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
    st.error("Por favor, selecione um usuario do dashboard principal primeiro.")
    st.stop()

user_id = st.session_state['user_id']

# Initialize engine
engine = FinanceEngine(st)
engine.set_user(user_id)

st.title("Metas Financeiras")
st.markdown("---")

# Create goal form
with st.expander("Criar Nova Meta", expanded=False):
    with st.form("goal_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            name = st.text_input("Nome da Meta")
        
        with col2:
            target_value = st.number_input("Valor Alvo (R$)", min_value=0.01, step=100.0, value=1000.0)
        
        with col3:
            monthly_target = st.number_input("Contribuicao Mensal (R$)", min_value=0.0, step=50.0, value=100.0)
        
        col4, col5 = st.columns(2)
        
        with col4:
            deadline = st.date_input("Prazo (opcional)")
        
        with col5:
            st.empty()  # Spacer
        
        submitted = st.form_submit_button("Criar Meta")
        
        if submitted and name and target_value:
            deadline_str = deadline.isoformat() if deadline else None
            create_goal(
                user_id=user_id,
                name=name,
                target_value=target_value,
                monthly_target=monthly_target,
                deadline=deadline_str
            )
            st.success(f"Meta '{name}' criada!")
            st.rerun()

# Display goals
st.subheader("Metas Atuais")

goals = get_goals(user_id)

if goals:
    # Goals impact analysis
    goals_impact = engine.calculate_goals_impact()
    total_progress = engine.calculate_total_goals_progress()
    
    # Overall progress
    st.markdown('<div class="goal-card">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Metas", total_progress['total_goals'])
    
    with col2:
        st.metric("Concluidas", total_progress['completed_goals'])
    
    with col3:
        st.metric("Alvo Total", f"R$ {total_progress['total_target']:.2f}")
    
    with col4:
        st.metric("Progresso Geral", f"{total_progress['overall_percentage']:.1f}%")
    
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
            st.success(f"Metas sao acessiveis! Mensal liquido: R$ {goals_impact['monthly_net']:.2f}, Requerido: R$ {goals_impact['total_monthly_target']:.2f}")
        else:
            st.warning(f"Metas excedem o fluxo de caixa mensal! Deficit: R$ {goals_impact['shortfall']:.2f}")
    
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
                
                st.caption(f"Alvo: R$ {target:.2f} | Progresso: R$ {progress:.2f}")
                
                if goal['monthly_target']:
                    st.caption(f"Contribuicao mensal: R$ {goal['monthly_target']:.2f}")
                
                if goal['deadline']:
                    deadline_date = datetime.fromisoformat(goal['deadline'])
                    days_remaining = (deadline_date - datetime.now()).days
                    st.caption(f"Prazo: {goal['deadline'][:10]} ({days_remaining} dias restantes)")
                
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
                    if st.button(f"Adicionar R$ 100", key=f"add_{goal['id']}"):
                        engine.update_goal_progress(goal['id'], 100)
                        st.success("Progresso atualizado!")
                        st.rerun()
                
                with col_btn2:
                    if st.button(f"Excluir", key=f"del_{goal['id']}"):
                        delete_goal(goal['id'])
                        st.success("Meta excluida!")
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Nenhuma meta ainda. Crie sua primeira meta acima!")

# Projections with goals
st.markdown("---")
st.subheader("Projeções com Metas")

projection_months = st.slider("Periodo de Projeção (meses)", 3, 12, 6)
projections = engine.project_with_goals(months=projection_months)

if projections['goal_monthly_contribution'] > 0:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Mensal Liquido Base", f"R$ {projections['base_monthly_net']:.2f}")
    
    with col2:
        st.metric("Contribuicoes de Metas", f"R$ {projections['goal_monthly_contribution']:.2f}")
    
    with col3:
        st.metric("Mensal Liquido Ajustado", f"R$ {projections['adjusted_monthly_net']:.2f}")
    
    st.markdown("### Saldo Projetado com Contribuicoes de Metas")
    
    for proj in projections['projections']:
        st.markdown(
            f"**Mes {proj['month']}**: R$ {proj['projected_balance']:.2f} "
            f"(apos R$ {proj['goal_contribution']:.2f} contribuicao)"
        )
else:
    st.info("Defina metas mensais para suas metas para ver projecoes.")

st.markdown("---")
st.caption(f"Pagina de metas atualizada em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
