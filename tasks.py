from extensions import mail, celery
from flask_mail import Message

@celery.task
def send_email_task(subject, sender, recipients, body):
    with mail.connect() as conn:
        msg = Message(subject, sender=sender, recipients=recipients)
        msg.html = body
        conn.send(msg)
