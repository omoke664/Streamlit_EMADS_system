import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from email.message import EmailMessage
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_welcome_email(email, first_name, username):
    """Send welcome email to new users"""
    try:
        msg = EmailMessage()
        msg["Subject"] = "👋 Welcome to EMADS!"
        msg["From"] = os.getenv("SMTP_SENDER")
        msg["To"] = email
        msg.set_content(f"""
        Welcome to EMADS, {first_name}!

        Your account has been created successfully with username: {username}

        You can now log in to access the Energy Monitoring & Anomaly Detection System.

        Best regards,
        The EMADS Team
        """)

        with smtplib.SMTP_SSL(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT"))) as smtp:
            smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
            smtp.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        return False

def send_reset_email(email, first_name, reset_token):
    """Send password reset email"""
    try:
        # Verify SMTP settings are available
        required_env_vars = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "SMTP_SENDER"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False

        # Log SMTP configuration (excluding password)
        logger.info(f"SMTP Configuration:")
        logger.info(f"Host: {os.getenv('SMTP_HOST')}")
        logger.info(f"Port: {os.getenv('SMTP_PORT')}")
        logger.info(f"User: {os.getenv('SMTP_USER')}")
        logger.info(f"Sender: {os.getenv('SMTP_SENDER')}")

        msg = EmailMessage()
        msg["Subject"] = "🔒 Reset Your EMADS Password"
        msg["From"] = os.getenv("SMTP_SENDER")
        msg["To"] = email
        
        # Build reset URL with the correct domain
        base_url = os.getenv("APP_URL", "https://appemadssystem-4wkeepimasudozx3efzs8z.streamlit.app")
        reset_url = f"{base_url}/reset_password?token={reset_token}"
        
        msg.set_content(f"""
        Hello {first_name},

        You have requested to reset your password for your EMADS account.

        Click the link below to reset your password:
        {reset_url}

        This link will expire in 24 hours.

        If you did not request this password reset, please ignore this email.

        Best regards,
        The EMADS Team
        """)

        # Send email
        try:
            with smtplib.SMTP_SSL(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT"))) as smtp:
                logger.info("Connecting to SMTP server...")
                smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
                logger.info("SMTP login successful")
                smtp.send_message(msg)
                logger.info(f"Reset email sent successfully to {email}")
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {str(e)}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error occurred: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during email sending: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Failed to send reset email: {str(e)}")
        return False 