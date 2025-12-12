# 📧 Gmail Setup for AstroSense OTP

## Quick Setup Guide

### Step 1: Get Gmail App Password

1. **Go to your Google Account**: https://myaccount.google.com/
2. **Security** → **2-Step Verification** (enable if not already)
3. **Security** → **App passwords**
4. **Generate app password** for "Mail"
5. **Copy the 16-character password** (like: `abcd efgh ijkl mnop`)

### Step 2: Update .env File

Edit `backend/.env` and replace these lines:

```bash
# Email Configuration for OTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_actual_email@gmail.com
SMTP_PASSWORD=your_16_character_app_password
FROM_EMAIL=your_actual_email@gmail.com
```

**Example:**
```bash
SMTP_USERNAME=john.doe@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
FROM_EMAIL=john.doe@gmail.com
```

### Step 3: Restart Backend

```bash
# Stop current backend (Ctrl+C)
# Then restart:
cd backend
python main.py
```

### Step 4: Test It!

1. Go to: `http://localhost:3000/dashboard`
2. Enter your Gmail address
3. Check your Gmail inbox for the OTP
4. Enter the 6-digit code to login

## 🔧 Troubleshooting

**If emails don't send:**
- Check Gmail spam folder
- Verify app password is correct (no spaces)
- Make sure 2-Step Verification is enabled
- Try generating a new app password

**Current Status:**
- ✅ System will fall back to console output if Gmail isn't configured
- ✅ You can still test with console OTPs while setting up Gmail
- ✅ Once Gmail is configured, real emails will be sent

## 🚀 Ready to Test

The system is running at:
- **Frontend**: http://localhost:3000/dashboard
- **Backend**: http://localhost:8000

Try logging in with any email - if Gmail isn't configured yet, check the backend console for the OTP code!