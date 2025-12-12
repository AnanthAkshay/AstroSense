"""
Robust async email sender for AstroSense
Uses aiosmtplib for better async support and error handling
"""
import os
import asyncio
from email.message import EmailMessage
import aiosmtplib
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Email configuration from environment
SMTP_HOST = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USERNAME")
SMTP_PASS = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("FROM_EMAIL", "noreply@astrosense.com")

# Debug: Print loaded config (remove in production)
if os.getenv("ENVIRONMENT") == "development":
    print(f"DEBUG - SMTP_USER loaded: {SMTP_USER}")
    print(f"DEBUG - SMTP_PASS loaded: {'***' if SMTP_PASS else 'None'}")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")


async def send_email(
    subject: str, 
    to: str, 
    body_html: str, 
    body_text: Optional[str] = None,
    timeout: int = 15
) -> Tuple[bool, Optional[str]]:
    """
    Send email using aiosmtplib with robust error handling
    
    Args:
        subject: Email subject
        to: Recipient email address
        body_html: HTML email body
        body_text: Plain text email body (optional)
        timeout: SMTP timeout in seconds
        
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    
    # Check if SMTP is configured
    if not SMTP_USER or not SMTP_PASS or SMTP_USER == 'your_email@gmail.com':
        return False, "SMTP not configured"
    
    try:
        # Create email message
        msg = EmailMessage()
        msg["From"] = SMTP_FROM
        msg["To"] = to
        msg["Subject"] = subject
        
        # Set content (prefer HTML with text fallback)
        if body_text:
            msg.set_content(body_text)
            msg.add_alternative(body_html, subtype="html")
        else:
            msg.set_content(body_html, subtype="html")
        
        logger.info(f"📧 Attempting to send email to {to}")
        
        # Use SMTP_SSL for port 465 (more reliable)
        if SMTP_PORT == 465:
            # SSL on connect (port 465) - recommended approach
            await aiosmtplib.send(
                msg,
                hostname=SMTP_HOST,
                port=SMTP_PORT,
                username=SMTP_USER,
                password=SMTP_PASS,
                use_tls=True,
                start_tls=False,
                timeout=timeout,
            )
        else:
            # STARTTLS (port 587)
            await aiosmtplib.send(
                msg,
                hostname=SMTP_HOST,
                port=SMTP_PORT,
                username=SMTP_USER,
                password=SMTP_PASS,
                start_tls=True,
                use_tls=False,
                timeout=timeout,
            )
        
        logger.info(f"✅ Email sent successfully to {to}")
        return True, None
        
    except aiosmtplib.errors.SMTPAuthenticationError as e:
        error_msg = f"SMTP Authentication failed: {e.smtp_code} {e.smtp_error}"
        logger.error(f"❌ {error_msg}")
        return False, error_msg
        
    except aiosmtplib.errors.SMTPRecipientsRefused as e:
        error_msg = f"Recipients refused: {e}"
        logger.error(f"❌ {error_msg}")
        return False, error_msg
        
    except aiosmtplib.errors.SMTPResponseException as e:
        error_msg = f"SMTP error: {e.smtp_code} {e.smtp_error}"
        logger.error(f"❌ {error_msg}")
        return False, error_msg
        
    except aiosmtplib.errors.SMTPConnectError as e:
        error_msg = f"SMTP connection failed: {e}"
        logger.error(f"❌ {error_msg}")
        return False, error_msg
        
    except asyncio.TimeoutError:
        error_msg = f"SMTP timeout after {timeout} seconds"
        logger.error(f"❌ {error_msg}")
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Unexpected email error: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return False, error_msg


async def send_otp_email(email: str, otp: str) -> Tuple[bool, str]:
    """
    Send OTP email with beautiful HTML template
    
    Args:
        email: Recipient email address
        otp: 6-digit OTP code
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    
    subject = "🚀 AstroSense Login Code"
    
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
    
    # Send email
    success, error = await send_email(subject, email, html_body, text_body)
    
    if success:
        # Mask email for privacy in logs
        masked_email = f"{email[:3]}***{email.split('@')[1]}"
        return True, f"OTP sent to {masked_email}"
    else:
        logger.warning(f"Email delivery failed for {email}: {error}")
        return False, "Failed to send OTP email. Please try again."


def test_smtp_config() -> dict:
    """
    Test SMTP configuration without sending email
    
    Returns:
        Dictionary with configuration status
    """
    config_status = {
        "smtp_host": SMTP_HOST,
        "smtp_port": SMTP_PORT,
        "smtp_user": SMTP_USER,
        "smtp_configured": bool(SMTP_USER and SMTP_PASS and SMTP_USER != 'your_email@gmail.com'),
        "from_email": SMTP_FROM
    }
    
    return config_status