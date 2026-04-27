import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import SENDER_EMAIL, SMTP_PASSWORD, SMTP_PORT, SMTP_SERVER, SMTP_USER

def send_otp_email(receiver_email, otp, type="verification"):
    """
    Sends an OTP email using SMTP.
    If credentials are not provided, it logs to file as a fallback.
    """
    subject = "Your Ride Share OTP Code"
    if type == "password_reset":
        subject = "Reset Your Ride Share Password"
        body = f"Hello,\n\nYour password reset code is: {otp}\n\nThis code will expire in 10 minutes.\n\nIf you did not request this, please ignore this email."
    elif type == "login_2fa":
        subject = "Your Ride Share Login Code"
        body = f"Hello,\n\nYour login verification code is: {otp}\n\nThis code will expire in 10 minutes.\n\nIf this was not you, please secure your account."
    else:
        body = f"Hello,\n\nYour verification code is: {otp}\n\nThis code will expire in 5 minutes.\n\nWelcome to Ride Share!"

    # Fallback to logging if no credentials
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"\n[MOCK EMAIL] To {receiver_email}: {otp} (No SMTP credentials configured)")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Successfully sent email to {receiver_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
