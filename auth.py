# auth.py

import streamlit as st
import bcrypt
from database import insert_user, get_user_by_username, init_db
from utils import hash_password, check_password

def register():
    st.title("Register")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    confirm_password = st.text_input("Confirm Password", type='password')
    role = st.selectbox("Select Role", ['user','group_admin','admin'])

    if st.button("Register"):
        if password != confirm_password:
            st.error("Passwords do not match.")
        elif not username or not password:
            st.error("Please fill out all fields.")
        else:
            # Check if username already exists
            existing_user = get_user_by_username(username)
            if existing_user:
                st.error("Username already exists.")
            else:
                password_hash = hash_password(password)
                insert_user(username, password_hash, role)
                st.success("User registered successfully. Please log in.")
                st.info("Go to the Login page.")

def login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        if not username or not password:
            st.error("Please enter your username and password.")
        else:
            user = get_user_by_username(username)
            if user:
                password_hash = user[2]
                if check_password(password, password_hash):
                    # Set session state
                    st.session_state.authenticated = True
                    st.session_state.user_id = user[0]
                    st.session_state.username = user[1]
                    st.session_state.role = user[3]
                    st.rerun()
                else:
                    st.error("Incorrect password.")
            else:
                st.error("User not found.")

def logout():
    st.session_state.authenticated = False
    for key in ['user_id', 'username', 'role']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash)

# Initialize the database (ensure tables are created)
init_db()