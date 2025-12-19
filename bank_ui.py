import streamlit as st
from supabase import create_client, Client

# --- CONNECT TO SUPABASE ---
URL = "https://lnlqplkchjobbkbcbfaq.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxubHFwbGtjaGpvYmJrYmNiZmFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYwNDEwMTQsImV4cCI6MjA4MTYxNzAxNH0.YiViz0eQfPNEVK-ZtLt0rjtgqCYkp5fsZVfMFTptm8s"

supabase: Client = create_client(URL, KEY)

st.title("🏦 Simple Bank App")

# --- SESSION STATE (The App's Memory) ---
# This keeps the user logged in even if they click buttons.
if "user" not in st.session_state:
    st.session_state.user = None

# --- SIDEBAR MENU ---
if st.session_state.user:
    menu = ["Dashboard", "Logout"]
else:
    menu = ["Login", "Signup"]
choice = st.sidebar.selectbox("Menu", menu)

# --- SIGNUP LOGIC ---
if choice == "Signup":
    st.subheader("Create Account")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Register"):
        # Supabase creates the user in the background
        res = supabase.auth.sign_up({"email": email, "password": password})
        st.success("Success! Now go to Login.")

# --- LOGIN LOGIC ---
elif choice == "Login":
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        try:
            # Check credentials
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
            st.success("Logged in!")
            st.rerun()
        except:
            st.error("Wrong Email or Password")

# --- DASHBOARD LOGIC ---
elif choice == "Dashboard":
    user_id = st.session_state.user.id
    
    # Get user data from our table
    res = supabase.table("bank_accounts").select("*").eq("user_id", user_id).execute()
    
    if not res.data:
        # If new user, ask for their name
        name = st.text_input("Enter your Name to start")
        if st.button("Create Profile"):
            supabase.table("bank_accounts").insert({"user_id": user_id, "name": name, "balance": 500}).execute()
            st.rerun()
    else:
        # Show Balance and Simple Buttons
        data = res.data[0]
        st.write(f"### Welcome, {data['name']}")
        st.metric("Balance", f"₹ {data['balance']}")
        
        amount = st.number_input("Amount", min_value=1)
        
        if st.button("Deposit"):
            new_bal = data['balance'] + amount
            supabase.table("bank_accounts").update({"balance": new_bal}).eq("user_id", user_id).execute()
            st.success(f"Deposited ₹{amount}")
            st.rerun()
            
        if st.button("Withdraw"):
            if amount <= data['balance']:
                new_bal = data['balance'] - amount
                supabase.table("bank_accounts").update({"balance": new_bal}).eq("user_id", user_id).execute()
                st.success(f"Withdrew ₹{amount}")
                st.rerun()
            else:
                st.error("Not enough money!")

# --- LOGOUT ---
elif choice == "Logout":
    st.session_state.user = None
    st.rerun()
