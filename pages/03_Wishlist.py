import streamlit as st
from core.database import (
    get_wishlist, create_wishlist_item, update_wishlist_item, 
    delete_wishlist_item, mark_wishlist_achieved
)
from core.engine import FinanceEngine

# Page configuration
st.set_page_config(
    page_title="FinOS",
    page_icon="💰",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .wishlist-card {
        background-color: #AED9C5;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    
    .priority-1 {
        border-left: 4px solid #9ABF17;
    }
    
    .priority-2 {
        border-left: 4px solid #D4DB7A;
    }
    
    .priority-3 {
        border-left: 4px solid #84BF93;
    }
    
    .achieved {
        opacity: 0.6;
        background-color: #DDECF1;
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

st.title("Lista de Desejos")
st.markdown("---")

# Create wishlist item form
with st.expander("Adicionar a Lista de Desejos", expanded=False):
    with st.form("wishlist_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            name = st.text_input("Nome do Item")
        
        with col2:
            price = st.number_input("Preco (R$)", min_value=0.01, step=10.0, value=100.0)
        
        with col3:
            priority = st.selectbox("Prioridade", [1, 2, 3], format_func=lambda x: {1: "Alta", 2: "Media", 3: "Baixa"}[x])
        
        submitted = st.form_submit_button("Adicionar a Lista")
        
        if submitted and name and price:
            create_wishlist_item(
                user_id=user_id,
                name=name,
                price=price,
                priority=priority
            )
            st.success(f"'{name}' adicionado a lista de desejos!")
            st.rerun()

# Display wishlist
st.subheader("Sua Lista de Desejos")

wishlist = get_wishlist(user_id)

if wishlist:
    # Calculate affordability
    affordability = engine.calculate_wishlist_affordability()
    
    # Summary
    total_price = sum([item['price'] for item in wishlist if item['status'] != 'achieved'])
    achieved_count = len([item for item in wishlist if item['status'] == 'achieved'])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Itens", len(wishlist))
    
    with col2:
        st.metric("Alcançados", achieved_count)
    
    with col3:
        st.metric("Valor Total", f"R$ {total_price:.2f}")
    
    st.markdown("---")
    
    # Affordability analysis
    if affordability:
        affordable_items = [item for item in affordability if item['affordable']]
        unaffordable_items = [item for item in affordability if not item['affordable']]
        
        if affordable_items:
            st.success(f"{len(affordable_items)} itens sao acessiveis com o fluxo de caixa atual")
        
        if unaffordable_items:
            st.warning(f"{len(unaffordable_items)} itens precisam de melhor fluxo de caixa para alcançar")
    
    st.markdown("---")
    
    # Display items
    for item in wishlist:
        with st.container():
            priority_class = f"priority-{item['priority']}"
            achieved_class = "achieved" if item['status'] == 'achieved' else ""
            
            st.markdown(f'<div class="wishlist-card {priority_class} {achieved_class}">', unsafe_allow_html=True)
            
            col_left, col_right = st.columns([3, 1])
            
            with col_left:
                priority_label = {1: "Alta", 2: "Media", 3: "Baixa"}[item['priority']]
                
                st.markdown(f"### {item['name']}")
                st.caption(f"Prioridade: {priority_label} | Preco: R$ {item['price']:.2f}")
                
                if item['status'] == 'achieved':
                    st.success("Alcançado!")
                else:
                    # Find affordability info
                    item_affordability = next((a for a in affordability if a['id'] == item['id']), None)
                    
                    if item_affordability:
                        if item_affordability['affordable']:
                            months = item_affordability['months_to_achieve']
                            est_date = item_affordability['estimated_date']
                            st.info(f"Atingivel em {months} mes(es) (est. {est_date})")
                        else:
                            st.warning("Nao acessivel com o fluxo de caixa atual")
            
            with col_right:
                if item['status'] != 'achieved':
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.button("Alcançar", key=f"achieve_{item['id']}"):
                            mark_wishlist_achieved(item['id'])
                            st.success("Marcado como alcançado!")
                            st.rerun()
                    
                    with col_btn2:
                        if st.button("Excluir", key=f"del_{item['id']}"):
                            delete_wishlist_item(item['id'])
                            st.success("Item excluido!")
                            st.rerun()
                else:
                    if st.button("Excluir", key=f"del_achieved_{item['id']}"):
                        delete_wishlist_item(item['id'])
                        st.success("Item excluido!")
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Sua lista de desejos esta vazia. Adicione seu primeiro item acima!")

# Affordability breakdown
if wishlist and affordability:
    st.markdown("---")
    st.subheader("Analise de Acessibilidade")
    
    if affordability:
        for item in affordability:
            if item['affordable']:
                st.markdown(
                    f"**{item['name']}**: {item['months_to_achieve']} meses "
                    f"(R$ {item['price']:.2f} / R$ {item['monthly_net']:.2f} por mes) "
                    f"→ Est. {item['estimated_date']}"
                )
            else:
                st.markdown(
                    f"**{item['name']}**: Nao acessivel "
                    f"(R$ {item['price']:.2f} necessario, mas o mensal liquido e R$ {item['monthly_net']:.2f})"
                )

st.markdown("---")
st.caption(f"Pagina de lista de desejos atualizada em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
