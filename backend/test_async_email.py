#!/usr/bin/env python3
"""
Test async email functionality
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Import after loading env vars
from utils.emailer import send_otp_email, test_smtp_config

async def test_email_system():
    """Test the async email system"""
    
    print("🔧 Testing AstroSense Async Email System")
    print("=" * 50)
    
    # Test SMTP configuration
    config = test_smtp_config()
    print(f"SMTP Host: {config['smtp_host']}:{config['smtp_port']}")
    print(f"SMTP User: {config['smtp_user']}")
    print(f"SMTP Configured: {config['smtp_configured']}")
    print(f"From Email: {config['from_email']}")
    print("-" * 50)
    
    if not config['smtp_configured']:
        print("❌ SMTP not configured - check your .env file")
        return False
    
    # Test sending OTP email
    test_email = config['smtp_user']  # Send to self
    test_otp = "123456"
    
    print(f"📧 Sending test OTP to {test_email}...")
    
    try:
        success, message = await send_otp_email(test_email, test_otp)
        
        if success:
            print(f"✅ {message}")
            print("📬 Check your inbox for the test email!")
            return True
        else:
            print(f"❌ Failed: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_email_system())