# group_admin.py

import streamlit as st
from database import (
    get_group_id_by_admin,
    get_group_member_count,
    get_group_members,
    get_group_member_requests,
    update_group_member_status,
    delete_group_member,
    get_polls_by_group,
    create_poll,
    add_option,
    get_vote_counts,
    get_poll_by_id,
    get_current_polls_by_group,
    get_user_by_id,
    create_connection,
)
from datetime import datetime
from chat import group_admin_chat
from auth import logout
import pandas as pd

def group_admin_dashboard():
    st.sidebar.title("Group Admin Dashboard")
    options = [
        "Dashboard",
        "Monitor Polls",
        "Create Poll",
        "Group Members",
        "Requests",
        "Chat",
        "Logout",
    ]
    choice = st.sidebar.selectbox("Select an option", options)

    if choice == "Dashboard":
        show_dashboard()
    elif choice == "Monitor Polls":
        monitor_polls()
    elif choice == "Create Poll":
        create_new_poll()
    elif choice == "Group Members":
        manage_group_members()
    elif choice == "Requests":
        manage_requests()
    elif choice == "Chat":
        group_admin_chat()
    elif choice == "Logout":
        logout()
    else:
        st.error("Invalid choice.")

def show_dashboard():
    st.header("Group Admin Dashboard")
    group_id = get_group_id_by_admin(st.session_state.user_id)
    if group_id:
        # Display group-specific stats
        member_count = get_group_member_count(group_id)
        st.subheader("Group Information")
        st.write(f"**Group ID:** {group_id}")
        st.write(f"**Number of Members:** {member_count}")
        
        # Display current polls in the group
        st.subheader("Current Group Polls")
        current_polls = get_current_polls_by_group(group_id)
        if current_polls:
            for poll in current_polls:
                st.write(f"**{poll['poll_question']}**")
                st.write(f"Start Time: {poll['start_time']}")
                st.write(f"End Time: {poll['end_time']}")
        else:
            st.info("No current polls in your group.")
    else:
        st.error("You are not assigned to any group.")

def monitor_polls():
    st.header("Monitor Group Polls")
    group_id = get_group_id_by_admin(st.session_state.user_id)
    if group_id:
        polls = get_polls_by_group(group_id)
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
            st.info("No polls available in your group.")
    else:
        st.error("You are not assigned to any group.")

def create_new_poll():
    st.header("Create a New Group Poll")
    poll_question = st.text_input("Poll Question:")
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
    option1 = st.text_input("Option 1:")
    option2 = st.text_input("Option 2:")
    option3 = st.text_input("Option 3 (optional):")
    option4 = st.text_input("Option 4 (optional):")

    if st.button("Create Poll"):
        if poll_question and option1 and option2 and start_datetime < end_datetime:
            creator_id = st.session_state.user_id
            group_id = get_group_id_by_admin(creator_id)
            if group_id:
                poll_id = create_poll(
                    poll_question,
                    is_public=False,
                    creator_id=creator_id,
                    group_id=group_id,
                    start_time=start_datetime,
                    end_time=end_datetime,
                )
                add_option(poll_id, option1)
                add_option(poll_id, option2)
                if option3:
                    add_option(poll_id, option3)
                if option4:
                    add_option(poll_id, option4)
                st.success("Poll created successfully.")
            else:
                st.error("You are not assigned to any group.")
        else:
            st.error("Please fill out all required fields.")

def manage_group_members():
    st.header("Manage Group Members")
    group_id = get_group_id_by_admin(st.session_state.user_id)
    if group_id:
        members = get_group_members(group_id, status='accepted')
        if members:
            member_options = [f"{member[0]}: {member[1]}" for member in members]
            selected_member_str = st.selectbox("Select a member:", member_options)
            selected_member_id = int(selected_member_str.split(":")[0])

            action = st.selectbox("Action:", ["View Details", "Remove Member"])
            if action == "View Details":
                user = get_user_by_id(selected_member_id)
                if user:
                    st.write(f"**Member ID:** {user[0]}")
                    st.write(f"**Username:** {user[1]}")
                    st.write(f"**Role:** {user[3]}")
                else:
                    st.error("User not found.")
            elif action == "Remove Member":
                if st.button("Remove Member"):
                    delete_group_member(group_id, selected_member_id)
                    st.success("Member removed from the group.")
                    st.rerun()
        else:
            st.info("No members in your group.")
    else:
        st.error("You are not assigned to any group.")

def manage_requests():
    st.header("Manage Join Requests")
    group_id = get_group_id_by_admin(st.session_state.user_id)
    if group_id:
        requests = get_group_member_requests(group_id)
        if requests:
            for request in requests:
                member_id = request[0]
                user_id = request[1]
                username = request[2]
                st.write(f"**Username:** {username}")
                accept = st.button(f"Accept {username}", key=f"accept_{member_id}")
                reject = st.button(f"Reject {username}", key=f"reject_{member_id}")
                if accept:
                    update_group_member_status(member_id, 'accepted')
                    st.success(f"{username} has been added to the group.")
                    st.rerun()
                if reject:
                    update_group_member_status(member_id, 'rejected')
                    st.info(f"{username}'s request has been rejected.")
                    st.rerun()
        else:
            st.info("No pending join requests.")
    else:
        st.error("You are not assigned to any group.")

# Additional helper functions if needed

