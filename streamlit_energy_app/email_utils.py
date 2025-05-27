import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

def get_email_config():
    """Get email configuration from environment variables with defaults"""
    config = {
        'smtp_server': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', '587')),
        'sender_email': os.getenv('SMTP_USER', ''),
        'sender_password': os.getenv('SMTP_PASS', '')
    }
    return config

def send_email(recipients, subject, message):
    """
    Send an email to the specified recipients.
    
    Args:
        recipients (list): List of recipient email addresses
        subject (str): Email subject
        message (str): Email message content
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Get email configuration
        config = get_email_config()
        
        # Check if email configuration is complete
        if not all([config['sender_email'], config['sender_password']]):
            st.warning("""
            Email notifications are not configured. To enable email notifications, please set the following environment variables:
            
            - SMTP_USER: Your Gmail address
            - SMTP_PASS: Your Gmail app password
            - SMTP_HOST: smtp.gmail.com (default)
            - SMTP_PORT: 587 (default)
            
            Note: For Gmail, you need to:
            1. Enable 2-Step Verification
            2. Generate an App Password
            3. Use that App Password here
            
            Until configured, notifications will only appear in the dashboard.
            """)
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = config['sender_email']
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject
        
        # Add message body
        msg.attach(MIMEText(message, 'plain'))
        
        # Create SMTP session
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['sender_email'], config['sender_password'])
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        return False

def send_welcome_email(recipient_email, first_name):
    """Send a welcome email to a new user"""
    subject = "Welcome to EMADS!"
    message = f"""
    Dear {first_name},

    Welcome to the Energy Management and Anomaly Detection System (EMADS)!

    Your account has been created successfully. You can now log in to access the system.

    Best regards,
    The EMADS Team
    """
    return send_email([recipient_email], subject, message)
        
