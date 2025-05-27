import streamlit as st 
from require_login import require_login
from db import get_user_collection, get_messages_collection, get_communications_collection
from email_utils import send_email 
import pandas as pd 
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart





def get_message_recipients():
    """Get recipients based on their notification preferences"""
    users = get_user_collection()
    recipients = []
    
    for user in users.find({"role": {"$in": ["admin", "manager"]}}):
        prefs = user.get("preferences", {})
        notifications = prefs.get("notifications", {})
        
        # Check if user has enabled dashboard notifications
        if notifications.get("dashboard", True):  # Default to True if not set
            recipients.append(user["email"])
    
    return recipients

def communications_page():
    require_login()

    st.title("Communications")
    st.markdown("""
        This page displays your messages and notifications.
        You can view and manage your communications here.
    """)
    
    # Get user from session
    user = st.session_state.get('user')
    if not user:
        st.error("Please log in to view your communications.")
        return
    
    # Get collections
    communications = get_communications_collection()
    users = get_user_collection()

    # Build list of possible recipients (only admins/managers except yourself)
    recipients = []
    for u in users.find({"role": {"$in": ["admin", "manager"]}, "username": {"$ne": user["username"]}}):
        label = f"{u['first_name']} {u['last_name']} ({u['role']})"
        recipients.append((label, u["username"], u["email"]))

    # Message sending form
    st.subheader("Send a Message")
    with st.form("msg_form", clear_on_submit=True):
        recipient = st.selectbox(
            "Send to...",
            [label for label, _, _ in recipients],
            format_func=lambda x: x
        )
        title = st.text_input("Subject")
        content = st.text_area("Your message")
        send = st.form_submit_button("📨 Send")

    if send and content.strip():
        # Look up username & email for the chosen label
        recipient_info = next(r for r in recipients if r[0] == recipient)
        rec_label, rec_username, rec_email = recipient_info
        
        # Create message document
        message = {
            "username": rec_username,
            "sender": user["username"],
            "title": title.strip() or "No Subject",
            "message": content.strip(),
            "type": "user_message",
            "timestamp": datetime.now(),
            "read": False
        }
        
        # Insert message
        communications.insert_one(message)
        st.success(f"Message sent to {rec_label}!")
        
        # Send email notification
        try:
            subject = f"[EMADS] New message from {user['username']}"
            body = f"""
            Hello {rec_label},
            
            You have received a new message in the EMADS portal from {user['username']}.
            
            Subject: {message['title']}
            Message: {message['message']}
            
            Please log in to view and respond to this message.
            
            — EMADS System
            """
            send_email([rec_email], subject, body)
            st.info(f"📧 Notification sent to {rec_label}'s email.")
        except Exception as e:
            st.error(f"Failed to send email notification: {str(e)}")

    st.markdown("---")

    # Get user's messages
    messages = list(communications.find({"username": user["username"]}).sort("timestamp", -1))
    
    if not messages:
        st.info("No messages found.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(messages)
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Add status column if it doesn't exist
    if 'read' not in df.columns:
        df['read'] = False
    
    # Convert read status to string status
    df['status'] = df['read'].map({True: 'Read', False: 'Unread'})
    
    # Filter options
    st.subheader("Filter Messages")
    col1, col2 = st.columns(2)
    
    with col1:
        # Message type filter
        message_types = ['All'] + sorted(df['type'].unique().tolist())
        selected_type = st.selectbox(
            "Message Type",
            message_types,
            index=0
        )
    
    with col2:
        # Status filter
        status_filter = st.multiselect(
            "Status",
            ['Read', 'Unread'],
            default=['Unread', 'Read']
        )

    # Apply filters
    if selected_type != 'All':
        df = df[df['type'] == selected_type]

    if status_filter:
        df = df[df['status'].isin(status_filter)]
    
    # Display message count
    st.metric("Total Messages", len(df))
    
    # Display messages
    st.subheader("Your Messages")
    
    for _, message in df.iterrows():
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Message content
                st.markdown(f"**{message['title']}**")
                if 'sender' in message:
                    st.caption(f"From: {message['sender']}")
                st.markdown(message['message'])
                st.caption(f"Received: {message['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            with col2:
                # Status and actions
                status_color = "green" if message['read'] else "red"
                st.markdown(f"<span style='color:{status_color}'>{message['status']}</span>", unsafe_allow_html=True)
                
                if not message['read']:
                    if st.button("Mark as Read", key=f"read_{message['_id']}"):
                        communications.update_one(
                            {"_id": message['_id']},
                            {"$set": {"read": True}}
                        )
                        st.rerun()
            
            st.divider()
    
    # Add refresh button
    if st.button("Refresh Messages"):
        st.rerun()

def send_email_notification(recipient_email, subject, message):
    """
    Send an email notification to the specified recipient.
    
    Args:
        recipient_email (str): Email address of the recipient
        subject (str): Email subject
        message (str): Email message content
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Get email configuration from environment variables
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        
        if not all([smtp_server, smtp_port, sender_email, sender_password]):
            st.error("Email configuration is incomplete. Please check environment variables.")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Add message body
        msg.attach(MIMEText(message, 'plain'))
        
        # Create SMTP session
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return True
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        return False
