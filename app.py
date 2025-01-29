# app.py

import streamlit as st
from auth import login, register, logout
from admin import admin_dashboard
from group_admin import group_admin_dashboard
from user import user_dashboard

def main():
    st.title("Voting Application")
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    menu = ["Login", "Register"]
    if st.session_state.authenticated:
        menu = ["Home", "Logout"]

    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Login":
        if not st.session_state.authenticated:
            login()
    elif choice == "Register":
        if not st.session_state.authenticated:
            register()
    elif choice == "Logout":
        logout()
    elif st.session_state.authenticated:
        role = st.session_state.role
        if role == 'admin':
            admin_dashboard()
        elif role == 'group_admin':
            group_admin_dashboard()
        elif role == 'user':
            user_dashboard()
    else:
        st.subheader("Please log in to continue.")

if __name__ == '__main__':
    main()