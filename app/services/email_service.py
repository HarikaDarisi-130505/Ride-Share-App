import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..config import SENDER_EMAIL, SMTP_PASSWORD, SMTP_PORT, SMTP_SERVER, SMTP_USER

SMTP_TIMEOUT_SECONDS = 4


def _build_otp_message(receiver_email, otp, otp_type="verification"):
    subject = "Your Ride Share OTP Code"
    if otp_type == "password_reset":
        subject = "Reset Your Ride Share Password"
        body = (
            f"Hello,\n\nYour password reset code is: {otp}\n\n"
            "This code will expire in 10 minutes.\n\n"
            "If you did not request this, please ignore this email."
        )
    elif otp_type == "login_2fa":
        subject = "Your Ride Share Login Code"
        body = (
            f"Hello,\n\nYour login verification code is: {otp}\n\n"
            "This code will expire in 10 minutes.\n\n"
            "If this was not you, please secure your account."
        )
    else:
        body = (
            f"Hello,\n\nYour verification code is: {otp}\n\n"
            "This code will expire in 5 minutes.\n\n"
            "Welcome to Ride Share!"
        )

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    return msg


def _normalized_smtp_password():
    return (SMTP_PASSWORD or "").replace(" ", "")


def _deliver_otp_email(receiver_email, otp, otp_type="verification"):
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"\n[MOCK EMAIL] To {receiver_email}: {otp} (No email provider configured)")
        return False

    try:
        msg = _build_otp_message(receiver_email, otp, otp_type=otp_type)
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS)
        server.starttls()
        server.login(SMTP_USER, _normalized_smtp_password())
        server.send_message(msg)
        server.quit()
        print(f"Successfully sent email to {receiver_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_otp_email(receiver_email, otp, type="verification", async_mode=True):
    """
    Sends an OTP email using SMTP.
    Returns immediately by default so auth responses do not block on SMTP.
    """
    if async_mode:
        threading.Thread(
            target=_deliver_otp_email,
            args=(receiver_email, otp, type),
            daemon=True,
        ).start()
        return True

    return _deliver_otp_email(receiver_email, otp, otp_type=type)
