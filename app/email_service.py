import smtplib
from email.message import EmailMessage

from . import config

def send_email(
    recipient: str,
    subject: str,
    body: str,
):
    """
    Send an email using Gmail SMTP.
    """

    message = EmailMessage()

    message["From"] = config.EMAIL_ADDRESS
    message["To"] = recipient
    message["Subject"] = subject

    message.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(
            config.EMAIL_ADDRESS,
            config.EMAIL_PASSWORD,
        )

        smtp.send_message(message)