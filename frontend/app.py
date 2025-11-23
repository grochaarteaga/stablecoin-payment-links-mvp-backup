import streamlit as st
import requests
from dotenv import load_dotenv
import os

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Stablecoin Payment Links",
    page_icon="💸",
    layout="centered",
)

# ------------------------------
# 🔍 1. Read URL query parameters
# ------------------------------

query_params = st.query_params  # Streamlit 1.30+
invoice_id_from_url = query_params.get("invoice_id", None)

st.title("💸 Stablecoin Payment Links MVP")


# ------------------------------
# 🔍 2. Display invoice detail view
# ------------------------------

def show_invoice(invoice_id: str):
    st.header("Invoice Details")

    try:
        res = requests.get(f"{BACKEND_URL}/api/invoices/{invoice_id}", timeout=10)
        res.raise_for_status()
        inv = res.json()

    except requests.HTTPError as http_err:
        if http_err.response.status_code == 404:
            st.error("❌ Invoice not found.")
        else:
            st.error(f"Server error: {http_err}")
        return

    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return

    st.subheader(f"Invoice {inv['id']}")
    st.write("**Amount:**", f"{inv['amount']} {inv['currency']}")
    st.write("**Memo:**", inv.get("memo") or "-")
    st.write("**Wallet:**", inv["merchant_wallet"])
    st.write("**Status:**", inv["status"])

    st.write("### Payment Link")
    st.markdown(f"[Click to open payment link]({inv['payment_link']})")


# ------------------------------
# 🔧 3. Normal app navigation
# ------------------------------

page = st.sidebar.radio("Navigation", ["Create Payment Request", "My Invoices"])


def create_invoice_view():
    st.header("Create Payment Request")

    amount = st.number_input("Amount", min_value=0.0, step=0.01)
    currency = st.selectbox("Currency", ["USD", "EUR", "PEN", "BRL", "ARS"])
    memo = st.text_input("Memo / Description", "")
    merchant_wallet = st.text_input("Merchant Wallet Address (Base USDC)")

    if st.button("Create Payment Link"):
        if amount <= 0 or not merchant_wallet:
            st.error("Amount must be > 0 and wallet is required.")
            return

        payload = {
            "amount": amount,
            "currency": currency,
            "memo": memo or None,
            "merchant_wallet": merchant_wallet,
        }

        try:
            res = requests.post(f"{BACKEND_URL}/api/invoices", json=payload, timeout=10)
            res.raise_for_status()
            data = res.json()
            st.success("Payment link created!")

            st.write("**Invoice ID:**", data["id"])
            st.write("**Payment link:**")
            st.markdown(f"[Open Payment Link]({data['payment_link']})")

        except requests.HTTPError as http_err:
            if http_err.response.status_code == 404:
                st.error("❌ Invoice not found.")
            else:
                st.error(f"Server error: {http_err}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")



def invoices_list_view():
    st.header("My Invoices")

    try:
        res = requests.get(f"{BACKEND_URL}/api/invoices", timeout=10)
        res.raise_for_status()
        invoices = res.json()
    except Exception as e:
        st.error(f"Error fetching invoices: {e}")
        return

    if not invoices:
        st.info("No invoices yet. Create one first.")
        return

    for inv in invoices:
        with st.expander(f"{inv['id']} - {inv['amount']} {inv['currency']} ({inv['status']})"):
            st.write("**Memo:**", inv.get("memo") or "-")
            st.write("**Wallet:**", inv["merchant_wallet"])
            st.write("**Payment link:**")
            st.markdown(f"[Open Payment Link]({inv['payment_link']})")


# ------------------------------
# 🔍 4. Routing logic
# ------------------------------

if invoice_id_from_url:
    # If URL contains invoice_id → show invoice directly
    show_invoice(invoice_id_from_url)
else:
    # Otherwise → normal UI
    if page == "Create Payment Request":
        create_invoice_view()
    else:
        invoices_list_view()
