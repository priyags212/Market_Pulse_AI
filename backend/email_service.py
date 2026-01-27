import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

# Configure dedicated logger for email service
logger = logging.getLogger("email_service")
logger.setLevel(logging.INFO)
# Avoid adding multiple handlers if reloaded
if not logger.handlers:
    file_handler = logging.FileHandler("email_notifications.log")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SMTP_EMAIL", "")
        self.sender_password = os.getenv("SMTP_PASSWORD", "")
        # Mock mode if no credentials provided
        self.mock_mode = not (self.sender_email and self.sender_password)

    def send_email(self, to_email: str, subject: str, body_html: str):
        if self.mock_mode:
            msg = f"[{'MOCK EMAIL'}] To: {to_email} | Subject: {subject} | Snippet: {body_html[:100]}..."
            print(msg)
            logger.info(msg)
            return True

        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body_html, 'html'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, to_email, text)
            server.quit()
            
            success_msg = f"Email sent to {to_email}"
            print(success_msg)
            logger.info(success_msg)
            return True
        except Exception as e:
            error_msg = f"Failed to send email to {to_email}: {e}"
            print(error_msg)
            logger.error(error_msg)
            return False
