import streamlit as st
from supabase import create_client, Client

# ============================================================
# 1. CLOUD CONNECTIVITY
# ============================================================
SUPABASE_URL = "https://lnlqplkchjobbkbcbfaq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxubHFwbGtjaGpvYmJrYmNiZmFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYwNDEwMTQsImV4cCI6MjA4MTYxNzAxNH0.YiViz0eQfPNEVK-ZtLt0rjtgqCYkp5fsZVfMFTptm8s"

# Initialize the gateway to the database
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Vivnovation Bank", layout="centered")

# --- STATE MANAGEMENT ---
# Why: Streamlit is 'stateless'. We use session_state to store the 
# User Object so we don't lose the login when the page refreshes.
if "user" not in st.session_state:
    st.session_state.user = None

st.title("🏦 Vivnovation Bank System")

# ============================================================
# 2. CORE LOGIC FUNCTIONS
# ============================================================

def sign_up(email, password):
    """Sends registration request to Supabase Auth."""
    return supabase.auth.sign_up({"email": email, "password": password})

def log_in(email, password):
    """Authenticates user and returns a session token."""
    return supabase.auth.sign_in_with_password({"email": email, "password": password})

# ============================================================
# 3. UI ROUTING
# ============================================================
if st.session_state.user:
    menu = ["Dashboard", "Logout"]
else:
    menu = ["Login", "Signup"]

choice = st.sidebar.selectbox("Menu", menu)

# ============================================================
# 4. SIGNUP MODULE
# ============================================================
if choice == "Signup":
    st.subheader("Register New Account")
    with st.form("signup", clear_on_submit=True):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Create Account"):
            try:
                # Logic: Call the auth API
                sign_up(email, password)
                st.success("Success! Now please go to the Login page.")
            except Exception as e:
                st.error(f"Error: {e}")

# ============================================================
# 5. LOGIN MODULE
# ============================================================
elif choice == "Login":
    st.subheader("Welcome Back")
    with st.form("login", clear_on_submit=True):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Log In"):
            try:
                res = log_in(email, password)
                # Logic: If successful, 'save' the user to our session
                if res.user:
                    st.session_state.user = res.user
                    st.success("Logged in! Switching to Dashboard...")
                    st.rerun()
            except Exception as e:
                # Handle 'Email not confirmed' or 'Invalid credentials'
                st.error(f"Login failed: {e}")

# ============================================================
# 6. DASHBOARD MODULE (THE BANKING CORE)
# ============================================================
elif choice == "Dashboard":
    user = st.session_state.user
    if not user:
        st.warning("Please login first.")
    else:
        # Step 1: Fetch bank data for the CURRENT user ID only.
        # This works because of the 'SELECT' policy you ran in SQL.
        try:
            res = supabase.table("bank_accounts").select("*").eq("user_id", user.id).execute()
            
            # Scenario: Profile doesn't exist yet
            if not res.data:
                st.info("No profile found. Let's open your account.")
                with st.form("setup", clear_on_submit=True):
                    name = st.text_input("Full Name")
                    acc_no = st.number_input("10-Digit Account Number", min_value=1000000000, max_value=9999999999)
                    if st.form_submit_button("Open Account"):
                        # Logic: This is the 'INSERT' that was failing.
                        # The SQL Policy 'auth.uid() = user_id' ensures you can only save your own ID.
                        supabase.table("bank_accounts").insert({
                            "user_id": user.id,
                            "name": name,
                            "account_number": int(acc_no),
                            "balance": 500
                        }).execute()
                        st.success("Account Created!")
                        st.rerun()
            
            # Scenario: Profile exists, show balance and transactions
            else:
                data = res.data[0]
                st.header(f"Hello, {data['name']}")
                st.metric("Current Balance", f"₹ {data['balance']}")
                
                with st.form("transact", clear_on_submit=True):
                    amt = st.number_input("Amount", min_value=1)
                    col1, col2 = st.columns(2)
                    
                    if col1.form_submit_button("Deposit"):
                        new_bal = data['balance'] + amt
                        supabase.table("bank_accounts").update({"balance": new_bal}).eq("id", data['id']).execute()
                        st.rerun()
                        
                    if col2.form_submit_button("Withdraw"):
                        if amt <= data['balance']:
                            new_bal = data['balance'] - amt
                            supabase.table("bank_accounts").update({"balance": new_bal}).eq("id", data['id']).execute()
                            st.rerun()
                        else:
                            st.error("Insufficient Balance")
        except Exception as e:
            st.error(f"Database Error: {e}")

# ============================================================
# 7. LOGOUT
# ============================================================
elif choice == "Logout":
    supabase.auth.sign_out()
    st.session_state.user = None
    st.success("Logged out.")
    st.rerun()
