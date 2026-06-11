import streamlit as st
from core.database import (
    get_wishlist, create_wishlist_item, update_wishlist_item, 
    delete_wishlist_item, mark_wishlist_achieved
)
from core.engine import FinanceEngine

# Page configuration
st.set_page_config(
    page_title="Wishlist - FinOS",
    page_icon="🎁",
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
    st.error("Please select a user from the main dashboard first.")
    st.stop()

user_id = st.session_state['user_id']

# Initialize engine
engine = FinanceEngine(st)
engine.set_user(user_id)

st.title("🎁 Wishlist")
st.markdown("---")

# Create wishlist item form
with st.expander("➕ Add to Wishlist", expanded=False):
    with st.form("wishlist_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            name = st.text_input("Item Name")
        
        with col2:
            price = st.number_input("Price (R$)", min_value=0.01, step=10.0, value=100.0)
        
        with col3:
            priority = st.selectbox("Priority", [1, 2, 3], format_func=lambda x: {1: "High", 2: "Medium", 3: "Low"}[x])
        
        submitted = st.form_submit_button("Add to Wishlist")
        
        if submitted and name and price:
            create_wishlist_item(
                user_id=user_id,
                name=name,
                price=price,
                priority=priority
            )
            st.success(f"'{name}' added to wishlist!")
            st.rerun()

# Display wishlist
st.subheader("Your Wishlist")

wishlist = get_wishlist(user_id)

if wishlist:
    # Calculate affordability
    affordability = engine.calculate_wishlist_affordability()
    
    # Summary
    total_price = sum([item['price'] for item in wishlist if item['status'] != 'achieved'])
    achieved_count = len([item for item in wishlist if item['status'] == 'achieved'])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Items", len(wishlist))
    
    with col2:
        st.metric("Achieved", achieved_count)
    
    with col3:
        st.metric("Total Value", f"R$ {total_price:.2f}")
    
    st.markdown("---")
    
    # Affordability analysis
    if affordability:
        affordable_items = [item for item in affordability if item['affordable']]
        unaffordable_items = [item for item in affordability if not item['affordable']]
        
        if affordable_items:
            st.success(f"✅ {len(affordable_items)} items are affordable with current cash flow")
        
        if unaffordable_items:
            st.warning(f"⚠️ {len(unaffordable_items)} items need better cash flow to achieve")
    
    st.markdown("---")
    
    # Display items
    for item in wishlist:
        with st.container():
            priority_class = f"priority-{item['priority']}"
            achieved_class = "achieved" if item['status'] == 'achieved' else ""
            
            st.markdown(f'<div class="wishlist-card {priority_class} {achieved_class}">', unsafe_allow_html=True)
            
            col_left, col_right = st.columns([3, 1])
            
            with col_left:
                status_emoji = "✅" if item['status'] == 'achieved' else "🎁"
                priority_label = {1: "High", 2: "Medium", 3: "Low"}[item['priority']]
                
                st.markdown(f"### {status_emoji} {item['name']}")
                st.caption(f"Priority: {priority_label} | Price: R$ {item['price']:.2f}")
                
                if item['status'] == 'achieved':
                    st.success("Achieved! 🎉")
                else:
                    # Find affordability info
                    item_affordability = next((a for a in affordability if a['id'] == item['id']), None)
                    
                    if item_affordability:
                        if item_affordability['affordable']:
                            months = item_affordability['months_to_achieve']
                            est_date = item_affordability['estimated_date']
                            st.info(f"📅 Achievable in {months} month(s) (est. {est_date})")
                        else:
                            st.warning("⚠️ Not affordable with current cash flow")
            
            with col_right:
                if item['status'] != 'achieved':
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.button("✅ Achieve", key=f"achieve_{item['id']}"):
                            mark_wishlist_achieved(item['id'])
                            st.success("Marked as achieved!")
                            st.rerun()
                    
                    with col_btn2:
                        if st.button("🗑️ Delete", key=f"del_{item['id']}"):
                            delete_wishlist_item(item['id'])
                            st.success("Item deleted!")
                            st.rerun()
                else:
                    if st.button("🗑️ Delete", key=f"del_achieved_{item['id']}"):
                        delete_wishlist_item(item['id'])
                        st.success("Item deleted!")
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Your wishlist is empty. Add your first item above!")

# Affordability breakdown
if wishlist and affordability:
    st.markdown("---")
    st.subheader("📊 Affordability Breakdown")
    
    if affordability:
        for item in affordability:
            if item['affordable']:
                st.markdown(
                    f"**{item['name']}**: {item['months_to_achieve']} months "
                    f"(R$ {item['price']:.2f} / R$ {item['monthly_net']:.2f} per month) "
                    f"→ Est. {item['estimated_date']}"
                )
            else:
                st.markdown(
                    f"**{item['name']}**: ❌ Not affordable "
                    f"(R$ {item['price']:.2f} needed, but monthly net is R$ {item['monthly_net']:.2f})"
                )
