import streamlit as st
from supabase import create_client, Client

# --- CONNECT TO SUPABASE ---
URL = "https://lnlqplkchjobbkbcbfaq.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxubHFwbGtjaGpvYmJrYmNiZmFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYwNDEwMTQsImV4cCI6MjA4MTYxNzAxNH0.YiViz0eQfPNEVK-ZtLt0rjtgqCYkp5fsZVfMFTptm8s"

import streamlit as st
from supabase import create_client, Client
import random
import pandas as pd

# --- CONNECT TO SUPABASE ---
URL = "https://lnlqplkchjobbkbcbfaq.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxubHFwbGtjaGpvYmJrYmNiZmFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYwNDEwMTQsImV4cCI6MjA4MTYxNzAxNH0.YiViz0eQfPNEVK-ZtLt0rjtgqCYkp5fsZVfMFTptm8s"

supabase: Client = create_client(URL, KEY)

st.title("🏦 Vivnovation Bank System")

# --- SESSION STATE (App Memory) ---
if "user" not in st.session_state:
    st.session_state.user = None

# --- SIDEBAR MENU ---
# We add "View Users" to the menu options
if st.session_state.user:
    menu = ["Dashboard", "View Users", "Logout"]
else:
    menu = ["Signup", "Login"]
choice = st.sidebar.selectbox("Menu", menu)

# ==========================================
# LOGIN & SIGNUP MODULES
# ==========================================
if choice == "Signup":
    st.subheader("Register Credentials")
    e = st.text_input("Email")
    p = st.text_input("Password", type="password")
    if st.button("Register"):
        supabase.auth.sign_up({"email": e, "password": p})
        st.success("Credentials saved! Now Login.")

elif choice == "Login":
    st.subheader("User Login")
    e = st.text_input("Email")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            res = supabase.auth.sign_in_with_password({"email": e, "password": p})
            st.session_state.user = res.user
            st.rerun()
        except:
            st.error("Invalid Login")

# ==========================================
# DASHBOARD: INDIVIDUAL PROFILE
# ==========================================
elif choice == "Dashboard":
    user_id = st.session_state.user.id
    res = supabase.table("bank_accounts").select("*").eq("user_id", user_id).execute()
    
    if not res.data:
        st.subheader("👤 Register User Details")
        with st.form("user_details_form", clear_on_submit=True):
            name = st.text_input("Full Name")
            age = st.number_input("Age", min_value=1, step=1)
            balance = st.number_input("Opening Balance", min_value=500)
            save_btn = st.form_submit_button("Save Details")
            
            if save_btn:
                if age < 18:
                    st.error("Error: Age must be 18 or above.")
                elif name == "":
                    st.warning("Please enter your name.")
                else:
                    generated_acc = f"VIV-{random.randint(100000, 999999)}"
                    supabase.table("bank_accounts").insert({
                        "user_id": user_id, "name": name, "age": int(age),
                        "account_number": generated_acc, "balance": balance
                    }).execute()
                    st.success("Details Saved Successfully!")
                    st.rerun()
    else:
        user_info = res.data[0]
        st.subheader("🏠 My Bank Profile")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Name:** {user_info['name']}")
            st.info(f"**Age:** {user_info['age']}")
        with col2:
            st.info(f"**Account No:** {user_info['account_number']}")
            st.info(f"**Status:** Verified")
        st.metric("Total Balance", f"₹ {user_info['balance']}")

# ==========================================
# VIEW USERS: ADMIN VIEW
# ==========================================
elif choice == "View Users":
    st.subheader("📋 Registered Bank Users")
    
    # Logic: Fetch ALL rows from the bank_accounts table
    response = supabase.table("bank_accounts").select("name, age, account_number, balance, created_at").execute()
    
    if response.data:
        # Convert the data into a Pandas DataFrame for a better table view
        df = pd.DataFrame(response.data)
        
        # Rename columns for a professional look
        df.columns = ["Name", "Age", "Account Number", "Balance (₹)", "Date Joined"]
        
        # Display the table
        st.dataframe(df, use_container_width=True)
        
        # Summary Metrics
        total_users = len(df)
        total_vault = df["Balance (₹)"].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Total Customers", total_users)
        c2.metric("Total Bank Deposits", f"₹ {total_vault}")
    else:
        st.warning("No users found in the database.")

# ==========================================
# LOGOUT
# ==========================================
elif choice == "Logout":
    st.session_state.user = None
    st.rerun()
