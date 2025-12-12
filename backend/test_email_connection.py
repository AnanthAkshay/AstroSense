"""Quick test script to verify Gmail SMTP connection"""
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")

print(f"Testing Gmail SMTP connection...")
print(f"User: {SMTP_USER}")
print(f"Password length: {len(SMTP_PASS) if SMTP_PASS else 0} chars")
print(f"Host: {SMTP_HOST}\n")

# Test 1: Port 587 with STARTTLS
print("Test 1: Port 587 with STARTTLS")
try:
    with smtplib.SMTP(SMTP_HOST, 587, timeout=15) as smtp:
        smtp.set_debuglevel(1)  # Enable debug output
        print("  - Connected to server")
        smtp.ehlo('localhost')
        print("  - EHLO sent")
        smtp.starttls()
        print("  - STARTTLS successful")
        smtp.ehlo('localhost')
        print("  - EHLO after STARTTLS")
        smtp.login(SMTP_USER, SMTP_PASS)
        print("  ✓ LOGIN successful!")
        
        # Send test email
        msg = EmailMessage()
        msg["Subject"] = "Test OTP - Connection Working"
        msg["From"] = SMTP_USER
        msg["To"] = SMTP_USER
        msg.set_content("If you receive this, email sending is working!")
        smtp.send_message(msg)
        print("  ✓ Test email sent successfully!")
        print("\n✓ Port 587 with STARTTLS WORKS!")
except Exception as e:
    print(f"  ✗ Failed: {e}\n")

# Test 2: Port 465 with SMTP_SSL
print("\nTest 2: Port 465 with SMTP_SSL")
try:
    with smtplib.SMTP_SSL(SMTP_HOST, 465, timeout=15) as smtp:
        smtp.set_debuglevel(1)
        print("  - Connected to server")
        smtp.ehlo('localhost')
        print("  - EHLO sent")
        smtp.login(SMTP_USER, SMTP_PASS)
        print("  ✓ LOGIN successful!")
        
        # Send test email
        msg = EmailMessage()
        msg["Subject"] = "Test OTP - Connection Working (SSL)"
        msg["From"] = SMTP_USER
        msg["To"] = SMTP_USER
        msg.set_content("If you receive this, email sending is working via SSL!")
        smtp.send_message(msg)
        print("  ✓ Test email sent successfully!")
        print("\n✓ Port 465 with SMTP_SSL WORKS!")
except Exception as e:
    print(f"  ✗ Failed: {e}\n")

print("\n" + "="*50)
print("Testing complete. Check your Gmail inbox for test emails.")
