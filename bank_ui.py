import streamlit as st
from supabase import create_client, Client

# ============================================================
# 1. INITIALIZATION & CONFIGURATION
# ============================================================

# The URL tells the code WHERE your database is hosted on the cloud.
SUPABASE_URL = "https://lnlqplkchjobbkbcbfaq.supabase.co"

# The ANON KEY is like a 'public key'. It allows the app to talk to Supabase.
# It is safe to use in frontend apps because we use Row Level Security (RLS) to protect data.
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxubHFwbGtjaGpvYmJrYmNiZmFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYwNDEwMTQsImV4cCI6MjA4MTYxNzAxNH0.YiViz0eQfPNEVK-ZtLt0rjtgqCYkp5fsZVfMFTptm8s"

# We initialize the 'client'. Think of this as the 'bridge' between your Python code and the Cloud.
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Basic Streamlit UI configuration
st.set_page_config(page_title="Secure Bank Prototype", layout="centered")
st.title("🏦 Vivnovation Bank System")

# ============================================================
# 2. AUTHENTICATION LOGIC (Managing Users)
# ============================================================

def signup_user(email, password):
    """
    Registers a user in the 'auth.users' table in Supabase.
    Supabase handles password hashing automatically (very secure).
    """
    return supabase.auth.sign_up({"email": email, "password": password})

def login_user(email, password):
    """
    Checks credentials against 'auth.users'.
    If correct, it returns a JWT (JSON Web Token).
    This token is stored inside the 'supabase' client object.
    """
    return supabase.auth.sign_in_with_password({"email": email, "password": password})

def get_current_user():
    """
    This function checks if the user is still 'authenticated'.
    It essentially looks for the JWT token.
    """
    return supabase.auth.get_user()

# ============================================================
# 3. UI NAVIGATION (Sidebar)
# ============================================================

menu = ["Signup", "Login", "Dashboard", "Logout"]
choice = st.sidebar.selectbox("Navigation Menu", menu)

# ============================================================
# 4. SIGNUP LOGIC (Creating an Account)
# ============================================================

if choice == "Signup":
    st.subheader("New User Registration")
    
    # We use st.form(clear_on_submit=True) to empty the input boxes after the button is clicked.
    with st.form("signup_form", clear_on_submit=True):
        email = st.text_input("Enter Email Address")
        password = st.text_input("Create Password", type="password")
        submit_btn = st.form_submit_button("Create My Account")
        
        if submit_btn:
            if email and password:
                try:
                    # Logic: Call the Supabase Auth API
                    result = signup_user(email, password)
                    st.success("Registration Successful! Please switch to the Login page.")
                except Exception as e:
                    st.error(f"Signup Failed: {str(e)}")
            else:
                st.warning("Both Email and Password are required.")

# ============================================================
# 5. LOGIN LOGIC (Accessing the System)
# ============================================================

elif choice == "Login":
    st.subheader("Secure Login")
    
    with st.form("login_form", clear_on_submit=True):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")
        
        if login_btn:
            try:
                # Logic: Validate with Supabase. 
                # If this fails (wrong password), it jumps to 'except'.
                result = login_user(email, password)
                st.success("Login Successful! You can now view your Dashboard.")
            except Exception as e:
                # Common Error: 'Email not confirmed' if you haven't turned it off in Supabase.
                st.error(f"Access Denied: {str(e)}")

# ============================================================
# 6. DASHBOARD (Bank Operations)
# ============================================================

elif choice == "Dashboard":
    # Step 1: Check if anyone is logged in.
    user_status = get_current_user()
    
    if not user_status or not user_status.user:
        st.warning("Session Expired or Not Logged In. Please go to the Login page.")
    else:
        # Step 2: Get the unique User ID (UUID) provided by Supabase Auth.
        uid = user_status.user.id
        
        # Step 3: Fetch the row from 'bank_accounts' where 'user_id' matches this UID.
        # This is where the 'Bank Data' lives.
        db_response = supabase.table("bank_accounts").select("*").eq("user_id", uid).execute()
        
        # Scenario A: User is logged in but hasn't set up a 'Bank Profile' yet.
        if not db_response.data:
            st.info("No bank profile found for this email. Let's create one.")
            with st.form("create_profile", clear_on_submit=True):
                u_name = st.text_input("Full Legal Name")
                u_age = st.number_input("Age", min_value=18)
                u_acc = st.number_input("Preferred Account Number", step=1)
                create_btn = st.form_submit_button("Open Account")
                
                if create_btn:
                    # Logic: Link the Auth User ID to this specific bank row.
                    supabase.table("bank_accounts").insert({
                        "user_id": uid,
                        "name": u_name,
                        "age": int(u_age),
                        "account_number": int(u_acc),
                        "balance": 500  # Minimum starting balance
                    }).execute()
                    st.success("Bank Profile Created! Please refresh the page.")
        
        # Scenario B: Bank profile exists. Show Balance and Transaction options.
        else:
            data = db_response.data[0] # Get the first (and only) row
            st.success(f"Verified User: {data['name']}")
            st.metric(label="Current Balance", value=f"₹ {data['balance']}")

            # Transaction Form
            with st.form("transaction_box", clear_on_submit=True):
                amount = st.number_input("Enter Amount", min_value=1)
                col1, col2 = st.columns(2)
                
                # Logic: Deposit adds to the current balance.
                if col1.form_submit_button("Deposit"):
                    new_bal = data['balance'] + amount
                    supabase.table("bank_accounts").update({"balance": new_bal}).eq("id", data['id']).execute()
                    st.rerun() # Refresh page to show new balance

                # Logic: Withdraw checks if user has enough money first.
                if col2.form_submit_button("Withdraw"):
                    if amount > data['balance']:
                        st.error("Insufficient Funds!")
                    else:
                        new_bal = data['balance'] - amount
                        supabase.table("bank_accounts").update({"balance": new_bal}).eq("id", data['id']).execute()
                        st.rerun()

# ============================================================
# 7. LOGOUT (Safety)
# ============================================================

elif choice == "Logout":
    # Clears the JWT token from the application memory.
    supabase.auth.sign_out()
    st.info("You have been securely logged out.")

