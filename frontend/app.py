import os

import pandas as pd
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Expense Tracker", page_icon="💸", layout="centered")
st.title("💸 Expense Tracker")

CATEGORIES = ["food", "transport", "housing", "fun", "health", "other"]


# ---------- Add expense ----------
st.subheader("Add expense")
col1, col2, col3 = st.columns([3, 1, 2])
with col1:
    description = st.text_input("Description", placeholder="pizza")
with col2:
    amount = st.number_input("Amount (₪)", min_value=0.0, step=1.0)
with col3:
    category = st.selectbox("Category", CATEGORIES)

if st.button("Add", type="primary"):
    if not description or amount <= 0:
        st.warning("Please enter a description and an amount greater than 0.")
    else:
        try:
            resp = requests.post(
                f"{BACKEND_URL}/expenses",
                json={"description": description, "amount": amount, "category": category},
                timeout=5,
            )
            resp.raise_for_status()
            st.success(f"Added: {description} ({amount}₪, {category})")
        except requests.RequestException as e:
            st.error(f"Failed to add expense: {e}")

st.divider()

# ---------- Load data ----------
try:
    expenses = requests.get(f"{BACKEND_URL}/expenses", timeout=5).json()
    summary = requests.get(f"{BACKEND_URL}/summary", timeout=5).json()
except requests.RequestException as e:
    st.error(f"Cannot reach backend at {BACKEND_URL}: {e}")
    st.stop()

# ---------- Summary chart ----------
st.subheader("Spending by category")
if summary:
    df_summary = pd.DataFrame(summary).set_index("category")
    st.bar_chart(df_summary["total"])
    st.metric("Total spent", f"{df_summary['total'].sum():,.2f} ₪")
else:
    st.info("No expenses yet - add your first one above!")

# ---------- Expense table + delete ----------
if expenses:
    st.subheader("All expenses")
    df = pd.DataFrame(expenses)[["id", "description", "amount", "category", "created_at"]]
    st.dataframe(df, use_container_width=True, hide_index=True)

    to_delete = st.selectbox(
        "Delete an expense",
        options=df["id"],
        format_func=lambda i: f"#{i} - {df.loc[df['id'] == i, 'description'].values[0]}",
    )
    if st.button("Delete selected"):
        resp = requests.delete(f"{BACKEND_URL}/expenses/{to_delete}", timeout=5)
        if resp.status_code == 204:
            st.success("Deleted!")
            st.rerun()
        else:
            st.error(f"Delete failed: {resp.status_code}")
