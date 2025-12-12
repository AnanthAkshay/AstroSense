"""
Simple synchronous Gmail sender using smtplib
More reliable than async version for Gmail
"""
import os
import smtplib
from email.message import EmailMessage
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

# Email configuration
SMTP_HOST = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USERNAME")
SMTP_PASS = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("FROM_EMAIL", "noreply@astrosense.com")


def send_otp_email_sync(email: str, otp: str) -> Tuple[bool, str]:
    """
    Send OTP email using synchronous Gmail SMTP
    More reliable than async version
    """
    
    # Check if SMTP is configured
    if not SMTP_USER or not SMTP_PASS or SMTP_USER == 'your_email@gmail.com':
        return False, "SMTP not configured"
    
    try:
        # Create email message
        msg = EmailMessage()
        msg["From"] = SMTP_FROM
        msg["To"] = email
        msg["Subject"] = "🚀 AstroSense Login Code"
        
        # Create HTML email body
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AstroSense Login Code</title>
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #0f172a; color: #ffffff; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 10px; padding: 30px; border: 1px solid #06b6d4;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #06b6d4; margin: 0; font-size: 28px;">🚀 AstroSense</h1>
                    <p style="color: #94a3b8; margin: 10px 0 0 0;">Space Weather Intelligence System</p>
                </div>
                
                <div style="background-color: #0f172a; border-radius: 8px; padding: 25px; text-align: center; margin: 20px 0;">
                    <h2 style="color: #06b6d4; margin: 0 0 15px 0;">Your Login Code</h2>
                    <div style="font-size: 36px; font-weight: bold; color: #ffffff; letter-spacing: 8px; font-family: 'Courier New', monospace; background-color: #1e293b; padding: 15px; border-radius: 5px; border: 2px solid #06b6d4;">
                        {otp}
                    </div>
                    <p style="color: #94a3b8; margin: 15px 0 0 0; font-size: 14px;">This code expires in 5 minutes</p>
                </div>
                
                <div style="background-color: #1e40af20; border-left: 4px solid #06b6d4; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; color: #94a3b8; font-size: 14px;">
                        <strong style="color: #06b6d4;">Security Notice:</strong> 
                        If you didn't request this code, please ignore this email. 
                        Never share your login codes with anyone.
                    </p>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #374151;">
                    <p style="color: #6b7280; font-size: 12px; margin: 0;">
                        AstroSense - Real-time Space Weather Monitoring<br>
                        This is an automated message, please do not reply.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version
        text_body = f"""
        AstroSense Login Code
        
        Your verification code is: {otp}
        
        This code will expire in 5 minutes.
        
        If you didn't request this code, please ignore this email.
        
        ---
        AstroSense - Space Weather Intelligence System
        """
        
        # Set content (prefer HTML with text fallback)
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")
        
        logger.info(f"📧 Sending OTP email to {email} via Gmail SMTP")
        
        # Use SMTP_SSL for port 465 (recommended for Gmail)
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
                smtp.login(SMTP_USER, SMTP_PASS)
                smtp.send_message(msg)
        else:
            # Use STARTTLS for port 587
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(SMTP_USER, SMTP_PASS)
                smtp.send_message(msg)
        
        logger.info(f"✅ Email sent successfully to {email}")
        masked_email = f"{email[:3]}***{email.split('@')[1]}"
        return True, f"Code sent to {masked_email}"
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"Gmail authentication failed: {e}"
        logger.error(f"❌ {error_msg}")
        return False, "Email authentication failed"
        
    except smtplib.SMTPRecipientsRefused as e:
        error_msg = f"Recipients refused: {e}"
        logger.error(f"❌ {error_msg}")
        return False, "Invalid email address"
        
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error: {e}"
        logger.error(f"❌ {error_msg}")
        return False, "Email delivery failed"
        
    except Exception as e:
        error_msg = f"Unexpected email error: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return False, "Email service error"