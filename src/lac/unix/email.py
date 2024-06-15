import os
from django.core.mail import EmailMessage
from django.conf import settings

# If this one returns None the mail was sent successfully
def send_mail(recipients: list, subject, message, attachment_path=""):
    if not are_mail_settings_configured():
        return "Email settings are not configured"
    email = EmailMessage(subject=subject, body=message, from_email=settings.EMAIL_HOST_EMAIL, to=recipients)
    # Check also if attachment_path exists
    if attachment_path != "" and attachment_path is not None and os.path.exists(attachment_path):
        email.attach_file(attachment_path)
    print("Sending email with subject: " + subject + " to: " + recipients)
    try:
        email.send()
    except Exception as e:
        error_message = "Error while sending email: " + str(e)
        print(error_message)
        return error_message
    

def are_mail_settings_configured():
    return settings.EMAIL_HOST_USER and settings.EMAIL_HOST_EMAIL and settings.EMAIL_HOST_PASSWORD and settings.EMAIL_HOST and settings.EMAIL_PORT

