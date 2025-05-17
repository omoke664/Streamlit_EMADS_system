import os, smtplib 
from email.message import EmailMessage 
from dotenv import load_dotenv 




load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")


def send_email(to_addrs: str, subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] =  to_addrs
    msg["Subject"] = subject
    msg.set_content(body)


    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()     #identify ourselves
        smtp.starttls()     # upgrade to encrypted
        smtp.ehlo()     # re-identify after TLS
        smtp.login(SMTP_USER, SMTP_PASS) 

        # Send mail explicitly
        smtp.send_message(msg) # issue MAIL/RCPT/DATA
        