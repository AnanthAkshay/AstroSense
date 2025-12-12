#!/usr/bin/env python3
"""
Test Gmail SMTP connection
"""
import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

def test_gmail_connection():
    """Test Gmail SMTP connection"""
    
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    from_email = os.getenv('FROM_EMAIL', '')
    
    print(f"🔧 Testing Gmail SMTP Connection")
    print(f"Server: {smtp_server}:{smtp_port}")
    print(f"Username: {smtp_username}")
    print(f"Password: {'*' * len(smtp_password) if smtp_password else 'NOT SET'}")
    print("-" * 50)
    
    if not smtp_username or not smtp_password:
        print("❌ SMTP credentials not configured")
        return False
    
    try:
        print("🔗 Connecting to Gmail SMTP...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        
        print("🔐 Starting TLS...")
        server.starttls()
        
        print("🔑 Logging in...")
        server.login(smtp_username, smtp_password)
        
        print("📧 Sending test email...")
        
        # Create test email
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = smtp_username  # Send to self
        msg['Subject'] = "🚀 AstroSense Email Test"
        
        body = """
        This is a test email from AstroSense!
        
        If you received this, Gmail SMTP is working correctly.
        
        Test OTP: 123456
        
        ---
        AstroSense Authentication System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        text = msg.as_string()
        server.sendmail(from_email, smtp_username, text)
        server.quit()
        
        print("✅ Email sent successfully!")
        print(f"📬 Check your inbox: {smtp_username}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("💡 Check your app password and make sure 2-step verification is enabled")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_gmail_connection()