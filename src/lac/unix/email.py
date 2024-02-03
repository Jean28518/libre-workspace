from django.core.mail import EmailMessage
from django.conf import settings

# If this one returns None the mail was sent successfully
def send_mail(recipient, subject, message, attachment_path=""):
    email = EmailMessage(subject=subject, body=message, from_email=settings.EMAIL_HOST_USER, to=[recipient])
    if attachment_path != "":
        email.attach_file(attachment_path)
    print("Sending email with subject: " + subject + " to: " + recipient)
    try:
        email.send()
    except Exception as e:
        error_message = "Error while sending email: " + str(e)
        print(error_message)
        return error_message