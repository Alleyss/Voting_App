# user.py

import streamlit as st
from database import (
    get_current_polls,
    get_options_by_poll,
    has_user_voted,
    cast_vote,
    get_vote_counts,
    add_group_member,
    get_group_by_name,
    get_group_members,
    get_group_member_requests,
    get_polls_user_can_see_results
)
from datetime import datetime
from auth import logout

def user_dashboard():
    st.sidebar.title("User Dashboard")
    menu = ["Vote", "See Results", "Join a Group", "Logout"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Vote":
        vote()
    elif choice == "See Results":
        see_results()
    elif choice == "Join a Group":
        join_group()
    elif choice == "Logout":
        logout()
    else:
        st.subheader("Welcome to the User Dashboard")

def vote():
    st.header("Available Polls")
    user_id = st.session_state.get('user_id')
    polls = get_current_polls(user_id)

    if polls:
        for poll in polls:
            poll_id = poll[0]
            poll_question = poll[1]
            is_public = poll[2]
            start_time = poll[5]
            end_time = poll[6]

            st.subheader(f"Poll: {poll_question}")
            st.write(f"Start Time: {start_time}")
            st.write(f"End Time: {end_time}")

            if has_user_voted(poll_id, user_id):
                st.info("You have already voted in this poll.")
            else:
                options = get_options_by_poll(poll_id)
                option_texts = [option[2] for option in options]
                option_ids = [option[0] for option in options]
                selected_option = st.radio("Choose an option:", option_texts, key=f"poll_{poll_id}")

                if st.button("Submit Vote", key=f"vote_{poll_id}"):
                    option_index = option_texts.index(selected_option)
                    selected_option_id = option_ids[option_index]
                    cast_vote(poll_id, selected_option_id, user_id)
                    st.success("Your vote has been recorded.")
    else:
        st.info("No available polls at this time.")

def see_results():
    st.header("Poll Results")
    user_id = st.session_state.get('user_id')
    polls = get_polls_user_can_see_results(user_id)

    if polls:
        # Build poll options for selectbox
        poll_options = [f"{poll['poll_id']}: {poll['poll_question']}" for poll in polls]
        selected_poll_str = st.selectbox("Select a poll to view results:", poll_options)
        selected_poll_id = int(selected_poll_str.split(":")[0])

        # Find the selected poll
        selected_poll = next((poll for poll in polls if poll['poll_id'] == selected_poll_id), None)

        if selected_poll:
            end_time_str = selected_poll['end_time']
            # Convert end_time_str to datetime object
            end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')

            now = datetime.now()

            if end_time <= now:
                # Poll has ended, show results
                results = get_vote_counts(selected_poll_id)
                if results:
                    option_texts = [result[0] for result in results]
                    vote_counts = [result[1] for result in results]
                    total_votes = sum(vote_counts)

                    if total_votes > 0:
                        st.subheader("Results")
                        for option_text, count in zip(option_texts, vote_counts):
                            percentage = (count / total_votes) * 100
                            st.write(f"{option_text}: {count} votes ({percentage:.2f}%)")
                            st.progress(percentage / 100)
                    else:
                        st.info("No votes have been cast in this poll yet.")
                else:
                    st.error("No options found for this poll.")
            else:
                # Poll is still active
                st.info("Poll is still active, come back after the end time to see the results.")
                st.write(f"Poll ends at: {end_time_str}")
        else:
            st.error("Poll not found.")
    else:
        st.info("No available polls to display.")
def join_group():
    st.header("Join a Group")
    group_name = st.text_input("Enter the name of the group you want to join:")
    if st.button("Request to Join"):
        group = get_group_by_name(group_name)
        if group:
            group_id = group[0]
            user_id = st.session_state.get('user_id')
            # Check if the user is already a member or has a pending request
            current_members = get_group_members(group_id, status='accepted')
            pending_members = get_group_members(group_id, status='pending')
            member_ids = [member[0] for member in current_members + pending_members]

            if user_id in member_ids:
                st.info("You have already requested to join this group or are already a member.")
            else:
                add_group_member(group_id, user_id, status='pending')
                st.success("Your request to join the group has been sent.")
        else:
            st.error("Group not found.")