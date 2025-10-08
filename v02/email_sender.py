import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

logger = logging.getLogger("stat2serg_logger")

class EmailSender:
    def __init__(self, smtp_server, email_account, email_password):
        self.smtp_server = smtp_server
        self.email_account = email_account
        self.email_password = email_password

    def send_email_with_attachment(self, receiver_email, subject, body, attachment_path):
        """
        Отправляет электронное письмо с вложением.
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_account
            msg['To'] = receiver_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Добавляем вложение
            if attachment_path:
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {attachment_path.split('/')[-1]}",
                )
                msg.attach(part)
            
            logger.info(f"Подключение к SMTP-серверу: {self.smtp_server}...")
            with smtplib.SMTP(self.smtp_server, 587) as server:
                server.starttls()
                server.login(self.email_account, self.email_password)
                server.send_message(msg)
            
            logger.info("✅ Письмо с файлом успешно отправлено.")
            return True
            
        except Exception as e:
            logger.error(f"❌ Не удалось отправить письмо: {e}")
            return False
