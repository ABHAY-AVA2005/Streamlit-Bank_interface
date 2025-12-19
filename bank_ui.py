import streamlit as st
from supabase import create_client, Client

# ============================================================
# 1. GLOBAL CONFIGURATION & API CONNECTIVITY
# ============================================================

# The URL is the unique cloud endpoint for your specific Supabase project.
SUPABASE_URL = "https://lnlqplkchjobbkbcbfaq.supabase.co"

# The ANON KEY is the 'Public API Key'. 
# It allows the frontend to interact with the database under the protection 
# of Row Level Security (RLS) policies.
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxubHFwbGtjaGpvYmJrYmNiZmFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYwNDEwMTQsImV4cCI6MjA4MTYxNzAxNH0.YiViz0eQfPNEVK-ZtLt0rjtgqCYkp5fsZVfMFTptm8s"

# We initialize the Supabase Client. This object acts as the gateway 
# for all Authentication and Database commands.
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuring the UI layout to be centered and professional.
st.set_page_config(page_title="Vivnovation Bank Prototype", layout="centered")

# --- PERSISTENT STATE MANAGEMENT ---
# Why: Streamlit reruns the whole script on every interaction.
# Without 'session_state', the app would 'forget' who is logged in 
# the moment you click a button.
if "user_token" not in st.session_state:
    st.session_state.user_token = None  # Stores the User ID (UUID) once logged in

st.title("🏦 Vivnovation Bank Management")
st.markdown("---")

# ============================================================
# 2. LOGIC FUNCTIONS (BACKEND OPERATIONS)
# ============================================================

def handle_signup(email, password):
    """
    Communicates with Supabase Auth.
    - Sends email/password over HTTPS.
    - Supabase hashes the password (standard security).
    - Returns a user object if successful.
    """
    return supabase.auth.sign_up({"email": email, "password": password})

def handle_login(email, password):
    """
    Verifies credentials with Supabase.
    - If valid, Supabase returns a 'Session' containing a JWT.
    - This session allows us to retrieve the unique User ID.
    """
    return supabase.auth.sign_in_with_password({"email": email, "password": password})

# ============================================================
# 3. DYNAMIC SIDEBAR NAVIGATION
# ============================================================

# Logic: If the user is logged in, show 'Dashboard'. 
# If not, only show 'Login' or 'Signup'.
if st.session_state.user_token:
    menu = ["Dashboard", "Logout"]
else:
    menu = ["Login", "Signup"]

choice = st.sidebar.selectbox("Navigate System", menu)

# ============================================================
# 4. SIGNUP MODULE
# ============================================================
if choice == "Signup":
    st.subheader("User Registration")
    
    # 'clear_on_submit=True' ensures that the input fields reset after the 
    # button is pressed, preventing duplicate entries or data leaking in the UI.
    with st.form("reg_form", clear_on_submit=True):
        email_input = st.text_input("Email Address")
        pass_input = st.text_input("Password", type="password")
        signup_btn = st.form_submit_button("Create Account")
        
        if signup_btn:
            try:
                # Trigger the Auth API call
                response = handle_signup(email_input, pass_input)
                st.success("Account created successfully! Please proceed to Login.")
            except Exception as e:
                # Catches errors like 'User already exists' or 'Password too short'
                st.error(f"Registration Failed: {e}")

# ============================================================
# 5. LOGIN MODULE
# ============================================================
elif choice == "Login":
    st.subheader("Secure Access")
    
    with st.form("auth_form", clear_on_submit=True):
        email_input = st.text_input("Email")
        pass_input = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Sign In")
        
        if login_btn:
            try:
                # Authenticate and retrieve session data
                auth_res = handle_login(email_input, pass_input)
                
                # Logic: We extract the unique ID (UUID) and save it to the Session State.
                # This 'remembers' the user for the rest of their session.
                st.session_state.user_token = auth_res.user
                st.success("Logged in! Opening Dashboard...")
                st.rerun() # Refresh page to show the Dashboard immediately
            except Exception as e:
                st.error(f"Login Error: {e}")

# ============================================================
# 6. DASHBOARD (BANKING CORE)
# ============================================================
elif choice == "Dashboard":
    # Security Check: Ensure a user object exists in memory
    user = st.session_state.user_token
    
    if not user:
        st.warning("No active session found. Please log in.")
    else:
        # Step 1: Query the 'bank_accounts' table using the current User's ID.
        # RLS policies in Supabase ensure you can only find YOUR row.
        db_query = supabase.table("bank_accounts").select("*").eq("user_id", user.id).execute()
        
        # Step 2: If the query returns nothing, the user hasn't created a 'Bank Profile'.
        if not db_query.data:
            st.info("New User detected. Please initialize your banking profile.")
            with st.form("profile_setup", clear_on_submit=True):
                full_name = st.text_input("Full Legal Name")
                acc_num = st.number_input("Desired Account Number", min_value=1000, step=1)
                init_btn = st.form_submit_button("Initialize Account")
                
                if init_btn:
                    # Logic: Insert new row linked to this User ID.
                    supabase.table("bank_accounts").insert({
                        "user_id": user.id,
                        "name": full_name,
                        "account_number": int(acc_num),
                        "balance": 500  # Default startup gift
                    }).execute()
                    st.success("Account opened! Please refresh Dashboard.")
                    st.rerun()
        
        # Step 3: If data exists, display the Bank Account UI.
        else:
            account_data = db_query.data[0]
            st.header(f"Welcome back, {account_data['name']}")
            
            # Display balance using a Metric widget for better visuals.
            st.metric("Total Balance", f"₹ {account_data['balance']}")
            
            with st.form("transaction_form", clear_on_submit=True):
                amount = st.number_input("Transaction Amount (₹)", min_value=1)
                c1, c2 = st.columns(2)
                
                if c1.form_submit_button("Deposit"):
                    # Logic: Calculate new balance and update the cloud DB.
                    updated_bal = account_data['balance'] + amount
                    supabase.table("bank_accounts").update({"balance": updated_bal}).eq("id", account_data['id']).execute()
                    st.success(f"Deposited ₹{amount}")
                    st.rerun()
                
                if c2.form_submit_button("Withdraw"):
                    # Logic: Validate that the user isn't withdrawing more than they have.
                    if amount > account_data['balance']:
                        st.error("Insufficient Funds!")
                    else:
                        updated_bal = account_data['balance'] - amount
                        supabase.table("bank_accounts").update({"balance": updated_bal}).eq("id", account_data['id']).execute()
                        st.success(f"Withdrew ₹{amount}")
                        st.rerun()

# ============================================================
# 7. LOGOUT MODULE
# ============================================================
elif choice == "Logout":
    # Step 1: Tell Supabase to invalidate the server-side session.
    supabase.auth.sign_out()
    # Step 2: Clear the local Session State memory.
    st.session_state.user_token = None
    st.info("Logged out successfully.")
    st.rerun()
