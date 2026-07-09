import streamlit as st

import config
from components.theme import inject_theme
from database.db import SessionLocal, init_db
from database.models import Inventory
from services.scheduler import start_scheduler

init_db()
start_scheduler()
inject_theme()

st.title("Inventory")
st.caption("Kit and T-shirt stock. Levels drop automatically when you hand items over on Candidate Detail.")


def _render_item(session, item: Inventory, label: str):
    with st.container(border=True):
        low_stock = item.quantity <= item.threshold
        st.markdown(f"**{label}**")
        if low_stock:
            st.markdown(
                f'<span style="color:#B91C1C; font-weight:700;">⚠ Low stock — {item.quantity} left '
                f'(reorder at {item.threshold})</span>',
                unsafe_allow_html=True,
            )
        else:
            st.caption(f"{item.quantity} in stock  ·  reorder at {item.threshold}")

        col1, col2, col3 = st.columns([1.2, 1, 1])
        with col1:
            add_qty = st.number_input(
                "Add to stock", min_value=0, step=1, value=0, key=f"add_{item.id}"
            )
        with col2:
            st.write("")
            if st.button("Add", key=f"add_btn_{item.id}", use_container_width=True):
                if add_qty > 0:
                    item.quantity += add_qty
                    if item.quantity > item.threshold:
                        item.low_stock_notified = False
                    session.commit()
                    st.rerun()
        with col3:
            new_threshold = st.number_input(
                "Low-stock alert at",
                min_value=0,
                step=1,
                value=item.threshold,
                key=f"threshold_{item.id}",
            )
            if new_threshold != item.threshold:
                item.threshold = new_threshold
                if item.quantity > item.threshold:
                    item.low_stock_notified = False
                session.commit()
                st.rerun()


session = SessionLocal()
try:
    kit = session.query(Inventory).filter(Inventory.item_type == "kit").first()
    if kit:
        _render_item(session, kit, "Onboarding kit")

    st.write("")
    st.subheader("T-shirts")
    tshirts = (
        session.query(Inventory)
        .filter(Inventory.item_type == "tshirt")
        .order_by(Inventory.size)
        .all()
    )
    size_order = {size: i for i, size in enumerate(config.TSHIRT_SIZES)}
    tshirts.sort(key=lambda t: size_order.get(t.size, 99))
    cols = st.columns(2)
    for i, tshirt in enumerate(tshirts):
        with cols[i % 2]:
            _render_item(session, tshirt, f"T-shirt · {tshirt.size}")
finally:
    session.close()
