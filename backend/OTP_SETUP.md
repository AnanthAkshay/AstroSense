# Gmail OTP Example - Standalone FastAPI Application

This is a minimal, complete FastAPI example for sending OTP (One-Time Password) codes via Gmail SMTP with proper error handling and troubleshooting fixes.

## Quick Setup

### 1. Install Dependencies

```bash
cd backend
pip install fastapi uvicorn sqlalchemy pydantic email-validator python-multipart python-dotenv
```

Or install all from requirements.txt (already includes most dependencies):
```bash
pip install -r requirements.txt
pip install python-multipart  # Add if not already installed
```

### 2. Create `.env` File

Create a `.env` file in the `backend` directory with:

```env
# Gmail OTP Configuration
SMTP_USER=you.sender@gmail.com
SMTP_PASS=your_16_char_app_password_here
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
OTP_TTL_SECONDS=600
```

**Important:**
- `SMTP_USER` should be your Gmail address
- `SMTP_PASS` should be a 16-character Gmail app password (not your regular password)
- Get app password from: https://myaccount.google.com/apppasswords
- Port 465 uses SMTP_SSL (recommended for Gmail)

### 3. Run the Application

```bash
cd backend
uvicorn otp_main:app --reload --port 8000
```

The API will be available at: `http://127.0.0.1:8000`

## API Endpoints

### 1. Request OTP (Login)

**POST** `/api/auth/login`

**Request:**
```json
{
  "email": "recipient@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Code sent to use***@example.com",
  "otp_session_id": 1,
  "email_delivery_ok": true,
  "email_error": null
}
```

### 2. Verify OTP

**POST** `/api/auth/verify`

**Request:**
```json
{
  "email": "recipient@example.com",
  "otp": "123456",
  "otp_session_id": 1
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Verified",
  "email": "recipient@example.com"
}
```

**Error Responses:**
- `404`: No active OTP session found
- `410`: OTP expired
- `401`: Wrong code
- `429`: Too many attempts (>10)

### 3. Resend OTP

**POST** `/api/auth/resend?otp_session_id=1`

**Request:**
```json
{
  "email": "recipient@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP resent",
  "resend_count": 1
}
```

**Error Responses:**
- `404`: OTP session not found
- `429`: Resend limit reached (max 2 resends per session)

## Testing with curl

### Request OTP:
```bash
curl -X POST "http://127.0.0.1:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"recipient@example.com"}'
```

### Verify OTP:
```bash
curl -X POST "http://127.0.0.1:8000/api/auth/verify" \
  -H "Content-Type: application/json" \
  -d '{"email":"recipient@example.com","otp":"123456","otp_session_id":1}'
```

### Resend OTP:
```bash
curl -X POST "http://127.0.0.1:8000/api/auth/resend?otp_session_id=1" \
  -H "Content-Type: application/json" \
  -d '{"email":"recipient@example.com"}'
```

## Testing with PowerShell

```powershell
# Request OTP
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"email":"recipient@example.com"}'

# Verify OTP
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/verify" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"email":"recipient@example.com","otp":"123456","otp_session_id":1}'
```

## Troubleshooting

### "Unexpected EOF" Error

This often indicates:
- **TLS/port mismatch**: Use `SMTP_SSL` on port 465 (already configured)
- **Wrong port**: Make sure `SMTP_PORT=465` in `.env`
- **Network/firewall blocking**: Some cloud providers block SMTP ports
- **Remote end closed connection**: Check Gmail account security settings

**Fix 1: Use SMTP_SSL on port 465 (already implemented)**
```python
# This is already in otp_main.py
with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
    smtp.login(SMTP_USER, SMTP_PASS)
    smtp.send_message(msg)
```

**Fix 2: Alternative - Port 587 with STARTTLS**
If port 465 doesn't work, you can modify `send_email_via_gmail()` to use port 587:
```python
with smtplib.SMTP(SMTP_HOST, 587) as smtp:
    smtp.ehlo()
    smtp.starttls()
    smtp.login(SMTP_USER, SMTP_PASS)
    smtp.send_message(msg)
```

### Authentication Failures

1. **Check SMTP_USER**: Must be your full Gmail address
2. **Check SMTP_PASS**: Must be the 16-character app password (not your regular password)
   - Remove any spaces when pasting
   - Generate new app password if unsure
3. **Check Gmail Security**: 
   - Check security notifications on the Gmail account
   - Google sometimes blocks new sign-ins - check your inbox for security alerts
   - Make sure 2-Step Verification is enabled (required for app passwords)

### Dev Fallback

If Gmail sending fails, the OTP will be printed to the server console:
```
DEV FALLBACK - OTP for recipient@example.com is: 123456
```

**⚠️ Remove this in production!** Never log plain OTPs in production logs.

### Email Not Received

- Check spam/junk folder
- Verify email address is correct
- Check Gmail account security inbox for blocked sign-in attempts
- Verify app password is still valid (regenerate if needed)

## Security Recommendations

1. **Remove dev fallback logging** in production - OTPs should never be logged
2. **Hash OTPs** - Store `HMAC(otp, salt)` instead of plain OTPs in the database
3. **Short TTL** - Use 5-15 minutes expiration
4. **Rate limiting** - Add rate limiting per IP for `/login` and `/verify` endpoints
5. **HTTPS** - Always use HTTPS in production
6. **Environment variables** - Never commit `.env` file to version control

## Database

The application uses SQLite with the database file `otp_auth.db` in the same directory as `otp_main.py`.

The database is automatically created on first run. OTP sessions are stored with:
- Email address
- OTP code
- Creation and expiration timestamps
- Verification status
- Resend count (max 2)
- Attempt count (max 10)

## Frontend Integration

### Flow:
1. User enters email → POST `/api/auth/login` → Get `otp_session_id`
2. Show OTP input screen
3. User enters OTP → POST `/api/auth/verify` → Handle response:
   - `401`: Show "Wrong code" error, allow re-entry
   - `410`: Show "Expired" with "Request new code" button
   - `200`: Success - proceed to authenticated state
4. Resend button → POST `/api/auth/resend` with `otp_session_id`
   - Show remaining resends: `2 - resend_count`
   - Disable when limit reached (`429`)

### UX Suggestions:
- Gray out resend button for 15s cooldown after click
- Show clear error messages from server
- Never display OTP value to users
- Show countdown timer for OTP expiration

## Alternative: Port 587 with STARTTLS

If port 465 doesn't work in your environment, you can modify the `send_email_via_gmail()` function:

```python
def send_email_via_gmail(to_email: str, otp: str) -> None:
    """Alternative: Use STARTTLS on port 587"""
    msg = EmailMessage()
    msg["Subject"] = "Your verification code"
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg.set_content(f"Your verification code is: {otp}\nIt expires in {OTP_TTL_SECONDS//60} minutes.")
    
    with smtplib.SMTP(SMTP_HOST, 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)
```

Then set `SMTP_PORT=587` in your `.env` file.

