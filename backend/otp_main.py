# main.py
import os
from datetime import datetime, timedelta
import random
import smtplib
from email.message import EmailMessage
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Config
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
OTP_TTL_SECONDS = int(os.getenv("OTP_TTL_SECONDS", "600"))  # 10 minutes

# DB setup (SQLite)
DATABASE_URL = "sqlite:///./otp_auth.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# Models
class OtpSession(Base):
    __tablename__ = "otp_sessions"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    otp_code = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    verified = Column(Boolean, default=False)
    resend_count = Column(Integer, default=0)
    attempts = Column(Integer, default=0)


Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="Gmail OTP Demo")


# Pydantic schemas
class EmailIn(BaseModel):
    email: EmailStr


class VerifyIn(BaseModel):
    email: EmailStr
    otp: str
    otp_session_id: Optional[int] = None


# Helpers
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_otp(length: int = 6) -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def send_email_via_gmail(to_email: str, otp: str) -> None:
    """Use Gmail SMTP. Try port 587 with STARTTLS first, fallback to 465 with SMTP_SSL."""
    msg = EmailMessage()
    msg["Subject"] = "Your verification code"
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg.set_content(
        f"Your verification code is: {otp}\nIt expires in {OTP_TTL_SECONDS//60} minutes."
    )

    # Try port 587 with STARTTLS first (often more reliable)
    if SMTP_PORT == 587 or SMTP_PORT == 465:
        try:
            # Try STARTTLS on port 587
            with smtplib.SMTP(SMTP_HOST, 587, timeout=15) as smtp:
                smtp.set_debuglevel(0)  # Set to 1 for debug output
                smtp.ehlo("localhost")  # Fix: Use valid hostname
                smtp.starttls()
                smtp.ehlo("localhost")  # Fix: Use valid hostname after STARTTLS
                smtp.login(SMTP_USER, SMTP_PASS)
                smtp.send_message(msg)
                return
        except Exception as e1:
            # Fallback to SMTP_SSL on port 465
            try:
                with smtplib.SMTP_SSL(SMTP_HOST, 465, timeout=15) as smtp:
                    smtp.ehlo("localhost")  # Fix: Use valid hostname
                    smtp.login(SMTP_USER, SMTP_PASS)
                    smtp.send_message(msg)
                    return
            except Exception as e2:
                # If both fail, raise the most specific error
                raise Exception(
                    f"STARTTLS(587) failed: {str(e1)} | SMTP_SSL(465) failed: {str(e2)}"
                )
    else:
        # Use configured port
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as smtp:
            smtp.ehlo("localhost")  # Fix: Use valid hostname
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)


# Endpoints
@app.post("/api/auth/login")
def login(payload: EmailIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    otp = generate_otp()
    now = datetime.utcnow()
    session = OtpSession(
        email=email,
        otp_code=otp,
        created_at=now,
        expires_at=now + timedelta(seconds=OTP_TTL_SECONDS),
        verified=False,
        resend_count=0,
        attempts=0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Try to send email. Use dev fallback: log OTP if send fails.
    try:
        send_email_via_gmail(email, otp)
        email_ok = True
        email_err = None
    except Exception as e:
        # Do NOT expose OTP in production logs; for dev only:
        print(f"DEV FALLBACK - OTP for {email} is: {otp}")  # remove in prod
        email_ok = False
        email_err = str(e)

    masked = email.split("@")[0][:3] + "***@" + email.split("@")[-1]
    return {
        "success": True,
        "message": f"Code sent to {masked}",
        "otp_session_id": session.id,
        "email_delivery_ok": email_ok,
        "email_error": email_err,
    }


@app.post("/api/auth/resend")
def resend(payload: EmailIn, otp_session_id: int, db: Session = Depends(get_db)):
    email = payload.email.lower()
    session = (
        db.query(OtpSession)
        .filter_by(id=otp_session_id, email=email, verified=False)
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=404, detail="OTP session not found. Request a new code."
        )
    if session.resend_count >= 2:
        raise HTTPException(
            status_code=429, detail="Resend limit reached (max 2). Start a new login."
        )
    # create new OTP for same session
    new_otp = generate_otp()
    session.otp_code = new_otp
    session.resend_count += 1
    session.created_at = datetime.utcnow()
    session.expires_at = datetime.utcnow() + timedelta(seconds=OTP_TTL_SECONDS)
    db.add(session)
    db.commit()
    db.refresh(session)

    try:
        send_email_via_gmail(email, new_otp)
        return {
            "success": True,
            "message": "OTP resent",
            "resend_count": session.resend_count,
        }
    except Exception as e:
        print(f"DEV FALLBACK - OTP for {email} is: {new_otp}")
        return {
            "success": False,
            "message": "Email failed - dev fallback used",
            "resend_count": session.resend_count,
            "error": str(e),
        }


@app.post("/api/auth/verify")
def verify(payload: VerifyIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    query = db.query(OtpSession).filter_by(email=email, verified=False)
    if payload.otp_session_id:
        query = query.filter_by(id=payload.otp_session_id)
    session = query.order_by(OtpSession.created_at.desc()).first()
    if not session:
        raise HTTPException(
            status_code=404, detail="No active OTP session found. Request a code first."
        )
    if datetime.utcnow() > session.expires_at:
        raise HTTPException(status_code=410, detail="OTP expired. Request a new code.")
    session.attempts += 1
    db.add(session)
    db.commit()
    if session.attempts > 10:
        raise HTTPException(
            status_code=429, detail="Too many attempts. Request a new code."
        )
    if payload.otp.strip() != session.otp_code:
        raise HTTPException(status_code=401, detail="Wrong code. Re-enter or resend.")

    # mark verified
    session.verified = True
    db.add(session)
    db.commit()

    # Return user object for frontend
    return {
        "success": True,
        "message": "Verified",
        "email": email,
        "user": {
            "email": email,
            "id": session.id,  # Using session id as temporary user id
            "created_at": (
                session.created_at.isoformat() if session.created_at else None
            ),
            "last_login": datetime.utcnow().isoformat(),
        },
    }
