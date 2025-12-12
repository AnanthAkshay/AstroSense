#!/usr/bin/env python3
"""
Test Gmail SMTP connection with multiple methods
"""
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

def test_gmail_methods():
    """Test different Gmail SMTP connection methods"""
    
    SMTP_USER = os.getenv("SMTP_USERNAME")
    SMTP_PASS = os.getenv("SMTP_PASSWORD")
    
    print("🔧 Testing Gmail SMTP Connection Methods")
    print("=" * 50)
    print(f"Username: {SMTP_USER}")
    print(f"Password: {'*' * len(SMTP_PASS) if SMTP_PASS else 'NOT SET'}")
    print("-" * 50)
    
    if not SMTP_USER or not SMTP_PASS:
        print("❌ Credentials not configured")
        return False
    
    # Create test email
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = SMTP_USER  # Send to self
    msg["Subject"] = "🚀 AstroSense Gmail Test"
    msg.set_content("This is a test email from AstroSense!\n\nIf you received this, Gmail SMTP is working!")
    
    # Test methods
    methods = [
        {
            "name": "SMTP_SSL (Port 465)",
            "func": lambda: smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)
        },
        {
            "name": "SMTP + STARTTLS (Port 587)", 
            "func": lambda: smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
        }
    ]
    
    for i, method in enumerate(methods, 1):
        print(f"\n🔗 Method {i}: {method['name']}")
        try:
            with method["func"]() as smtp:
                print("  ✓ Connection established")
                
                if "587" in method["name"]:
                    print("  ✓ Starting TLS...")
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.ehlo()
                
                print("  ✓ Logging in...")
                smtp.login(SMTP_USER, SMTP_PASS)
                
                print("  ✓ Sending test email...")
                smtp.send_message(msg)
                
                print(f"  ✅ SUCCESS! Method {i} works!")
                print(f"  📬 Check inbox: {SMTP_USER}")
                return True
                
        except smtplib.SMTPAuthenticationError as e:
            print(f"  ❌ Authentication failed: {e}")
        except smtplib.SMTPConnectError as e:
            print(f"  ❌ Connection failed: {e}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n❌ All methods failed!")
    print("\n💡 Troubleshooting tips:")
    print("1. Check if 2-step verification is enabled on Gmail")
    print("2. Verify the app password is correct (16 characters)")
    print("3. Try generating a new app password")
    print("4. Check if your network blocks SMTP ports")
    
    return False

if __name__ == "__main__":
    test_gmail_methods()