# admin.py

import streamlit as st
from database import (
    get_user_count,
    get_group_count,
    get_poll_count,
    get_active_user_count,
    get_all_polls,
    get_poll_by_id,
    create_poll,
    add_option,
    get_users_by_role,
    insert_user,
    update_user_role,
    delete_user,
    get_all_users,
    create_group,
    get_user_by_id,get_user_by_username,create_connection
)

from datetime import datetime, date, time
from chat import admin_chat
from auth import logout
import pandas as pd
from utils import hash_password
def admin_dashboard():
    st.sidebar.title("Admin Dashboard")
    options = [
        "Dashboard",
        "Monitor Polls",
        "Create Public Poll",
        "Create Private Poll",
        "Manage Group Admins",
        "Chat",
        "Logout",
    ]
    choice = st.sidebar.selectbox("Select an option", options)

    if choice == "Dashboard":
        show_dashboard()
    elif choice == "Monitor Polls":
        monitor_polls()
    elif choice == "Create Public Poll":
        create_new_poll(is_public=True)
    elif choice == "Create Private Poll":
        create_new_poll(is_public=False)
    elif choice == "Manage Group Admins":
        manage_group_admins()
    elif choice == "Chat":
        admin_chat()
    elif choice == "Logout":
        logout()
    else:
        st.error("Invalid choice.")

def show_dashboard():
    st.header("Admin Dashboard")
    # Display general data
    user_count = get_user_count()
    group_count = get_group_count()
    poll_count = get_poll_count()
    active_user_count = get_active_user_count()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Total Users")
        st.info(user_count)
    with col2:
        st.subheader("Total Groups")
        st.info(group_count)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Total Polls")
        st.info(poll_count)
    with col4:
        st.subheader("Active Users")
        st.info(active_user_count)

    # Display live poll details
    st.subheader("Live Polls")
    current_polls = get_current_polls_admin()
    if current_polls:
        for poll in current_polls:
            st.write(f"**{poll['poll_question']}**")
            st.write(f"Start Time: {poll['start_time']}")
            st.write(f"End Time: {poll['end_time']}")
    else:
        st.info("No live polls at the moment.")

def monitor_polls():
    st.header("Monitor Polls")
    polls = get_all_polls()
    if polls:
        poll_options = [f"{poll[0]}: {poll[1]}" for poll in polls]
        selected_poll_str = st.selectbox("Select a poll to monitor:", poll_options)
        selected_poll_id = int(selected_poll_str.split(":")[0])

        poll = get_poll_by_id(selected_poll_id)
        if poll:
            st.subheader(f"Poll: {poll['poll_question']}")
            results = get_vote_counts(selected_poll_id)
            if results:
                df = pd.DataFrame(results, columns=["Option", "Votes"])
                st.bar_chart(df.set_index("Option"))
                st.table(df)
            else:
                st.info("No votes have been cast in this poll yet.")
        else:
            st.error("Poll not found.")
    else:
        st.info("No polls available.")

def create_new_poll(is_public):
    st.header("Create a New Poll")
    poll_question = st.text_input("Poll Question:")
       # Start Date and Time
    start_date = st.date_input("Start Date", datetime.now().date(),key='start_date')
    start_time = st.time_input("Start Time", key='start_time')

    # End Date and Time
    end_date = st.date_input("End Date", datetime.now().date(),key='end_date')
    end_time = st.time_input("End Time", key='end_time')
    # Combine date and time into datetime objects
    start_datetime = datetime.combine(start_date, start_time)
    end_datetime = datetime.combine(end_date, end_time)
    if start_datetime >= end_datetime:
        st.warning("End time must be after start time.")

    if not is_public:
        # For private polls, select groups
        groups = get_all_groups()
        if groups:
            group_options = [f"{group[0]}: {group[1]}" for group in groups]
            selected_group_str = st.selectbox("Select a group:", group_options)
            group_id = int(selected_group_str.split(":")[0])
        else:
            st.info("No groups available.")
            return
    else:
        group_id = None  # Public poll

    options = []
    option1 = st.text_input("Option 1:")
    option2 = st.text_input("Option 2:")
    option3 = st.text_input("Option 3 (optional):")
    option4 = st.text_input("Option 4 (optional):")

    if st.button("Create Poll"):
        if poll_question and option1 and option2 and start_time < end_time:
            creator_id = st.session_state.user_id
            poll_id = create_poll(
                poll_question, is_public, creator_id, group_id, start_datetime, end_datetime
            )
            add_option(poll_id, option1)
            add_option(poll_id, option2)
            if option3:
                add_option(poll_id, option3)
            if option4:
                add_option(poll_id, option4)
            st.success("Poll created successfully.")
        else:
            st.error("Please fill out all required fields.")

def manage_group_admins():
    st.header("Manage Group Admins")
    menu = ["Create Group Admin", "View/Edit Group Admins"]
    choice = st.selectbox("Select an action:", menu)

    if choice == "Create Group Admin":
        create_group_admin()
    elif choice == "View/Edit Group Admins":
        view_edit_group_admins()

def create_group_admin():
    st.subheader("Create a Group Admin")
    username = st.text_input("Username:")
    password = st.text_input("Password:", type="password")
    confirm_password = st.text_input("Confirm Password:", type="password")
    group_name = st.text_input("Group Name:")

    if st.button("Create Group Admin"):
        if password != confirm_password:
            st.error("Passwords do not match.")
        elif not username or not password or not group_name:
            st.error("Please fill out all fields.")
        else:
            # Check if username already exists
            existing_user = get_user_by_username(username)
            if existing_user:
                st.error("Username already exists.")
            else:
                password_hash = hash_password(password)
                user_id = insert_user(username, password_hash, role="group_admin")
                # Create group and assign to group admin
                group_id = create_group(group_name, user_id)
                st.success("Group admin and group created successfully.")

def view_edit_group_admins():
    st.subheader("View/Edit Group Admins")
    group_admins = get_users_by_role("group_admin")
    if group_admins:
        admin_options = [f"{admin[0]}: {admin[1]}" for admin in group_admins]
        selected_admin_str = st.selectbox("Select a group admin:", admin_options)
        selected_admin_id = int(selected_admin_str.split(":")[0])

        admin = get_user_by_id(selected_admin_id)
        if admin:
            st.write(f"**Username:** {admin[1]}")
            st.write(f"**User ID:** {admin[0]}")

            action = st.selectbox("Action:", ["Update Role", "Delete Group Admin"])
            if action == "Update Role":
                new_role = st.selectbox("Select new role:", ["admin", "group_admin", "user"])
                if st.button("Update Role"):
                    update_user_role(selected_admin_id, new_role)
                    st.success("Role updated successfully.")
            elif action == "Delete Group Admin":
                if st.button("Delete"):
                    delete_user(selected_admin_id)
                    st.success("Group admin deleted successfully.")
        else:
            st.error("Group admin not found.")
    else:
        st.info("No group admins found.")

# Additional helper functions (to be placed within admin.py or imported)

def get_current_polls_admin():
    """Retrieve current polls for the admin dashboard."""
    now = datetime.now()
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM Polls WHERE start_time <= ? AND end_time >= ?
        ''', (now, now))
        polls = cursor.fetchall()
        # Convert to list of dictionaries for easier handling
        poll_list = []
        for poll in polls:
            poll_dict = {
                'poll_id': poll[0],
                'poll_question': poll[1],
                'is_public': bool(poll[2]),
                'creator_id': poll[3],
                'group_id': poll[4],
                'start_time': poll[5],
                'end_time': poll[6],
            }
            poll_list.append(poll_dict)
        return poll_list

def get_vote_counts(poll_id):
    """Retrieve vote counts for a specific poll."""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT Options.option_text, COUNT(Votes.vote_id) as vote_count FROM Options
            LEFT JOIN Votes ON Options.option_id = Votes.option_id
            WHERE Options.poll_id = ?
            GROUP BY Options.option_id
        ''', (poll_id,))
        results = cursor.fetchall()
        return results

def get_all_groups():
    """Retrieve all groups."""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Groups')
        groups = cursor.fetchall()
        return groups