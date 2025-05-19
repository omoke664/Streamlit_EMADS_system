# test_email.py
from email_utils import send_email

if __name__ == "__main__":
    send_email("ochiengileywesl@gmail.com",
               "Test from EMADS",
               "If you see this, STARTTLS is working!")
    print("Sent!")
