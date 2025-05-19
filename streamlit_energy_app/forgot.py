import smtplib
from email.message import EmailMessage
from auth_utils import generate_reset_token
import streamlit as st 
from db import get_user_collection 
import os 


def forgot_password_page():
    st.title("🔑 Forgot Password")
    users = get_user_collection()

    email = st.text_input("Enter your account email")
    if st.button("Send reset link"):
        if not users.find_one({"email": email}):
            st.error("No account found with that email.")
        else:
            token = generate_reset_token(email)
            # build a URL to your app + token param:
            reset_url = f"https://appemadssystem-4wkeepimasudozx3efzs8z.streamlit.app/?reset={token}"
            # send email:
            msg = EmailMessage()
            msg["Subject"] = "🔒 Password Reset"
            msg["From"] = os.getenv("SMTP_SENDER")
            msg["To"] = email
            msg.set_content(f"Click here to reset your password:\n\n{reset_url}\n\nLink expires in 1 hour.")
            try:
                with smtplib.SMTP_SSL(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT"))) as smtp:
                    smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
                    smtp.send_message(msg)
                st.success("✅ Reset link sent! Check your email.")
            except Exception as e:
                st.error(f"❌ Could not send email: {e}")
