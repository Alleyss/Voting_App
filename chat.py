# chat.py

import streamlit as st
from datetime import datetime
from database import send_message, get_messages, get_all_users, get_user_by_id
from auth import logout

def admin_chat():
    st.header("Admin Chat")
    # Admin can select any user to chat with
    users = get_all_users()
    users_dict = {f"{user[1]} (ID: {user[0]})": user[0] for user in users if user[0] != st.session_state.user_id}
    user_list = list(users_dict.keys())

    if user_list:
        selected_user = st.sidebar.selectbox("Select a user to chat with:", user_list)
        receiver_id = users_dict[selected_user]
        chat_interface(st.session_state.user_id, receiver_id)
    else:
        st.info("No other users available to chat with.")

def group_admin_chat():
    st.header("Chat with Admin")
    # Group admin can only chat with admin(s)
    # Assuming admins have the role 'admin'
    admins = [user for user in get_all_users() if user[2] == 'admin']
    admins_dict = {f"{admin[1]} (ID: {admin[0]})": admin[0] for admin in admins}

    if admins_dict:
        selected_admin = st.sidebar.selectbox("Select an admin to chat with:", list(admins_dict.keys()))
        receiver_id = admins_dict[selected_admin]
        chat_interface(st.session_state.user_id, receiver_id)
    else:
        st.info("No admins available to chat with.")

def chat_interface(sender_id, receiver_id):
    st.subheader(f"Chat with {get_user_by_id(receiver_id)[1]}")
    # Display chat history
    messages = get_messages(sender_id, receiver_id)
    if messages:
        for message in messages:
            sender_name = get_user_by_id(message[1])[1]
            timestamp = message[4]
            message_text = message[3]
            if message[1] == sender_id:
                st.write(f"**You:** {message_text}  _({timestamp})_")
            else:
                st.write(f"**{sender_name}:** {message_text}  _({timestamp})_")
    else:
        st.info("No messages yet. Start the conversation!")

    # Input for new message
    message_text = st.text_input("Type your message:")
    if st.button("Send"):
        if message_text.strip():
            send_message(sender_id, receiver_id, message_text.strip())
            st.rerun()  # Refresh to display the new message
        else:
            st.warning("Please enter a message before sending.")