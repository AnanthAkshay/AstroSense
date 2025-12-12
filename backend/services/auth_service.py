"""
Authentication Service for AstroSense
Simple email OTP authentication
"""
import secrets
import hashlib
import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import os
import logging

from database.manager import DatabaseManager
from models.auth import User, Session, OTP, AuthResponse

logger = logging.getLogger(__name__)


class AuthService:
    """Simple authentication service with email OTP"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@astrosense.com')
    
    def generate_otp(self) -> str:
        """Generate a 6-digit OTP"""
        return f"{secrets.randbelow(1000000):06d}"
    
    def hash_otp(self, otp: str) -> str:
        """Hash OTP using bcrypt"""
        return bcrypt.hashpw(otp.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_otp_hash(self, otp: str, otp_hash: str) -> bool:
        """Verify OTP against hash"""
        return bcrypt.checkpw(otp.encode('utf-8'), otp_hash.encode('utf-8'))
    
    def generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    def send_otp_email(self, email: str, otp: str) -> bool:
        """Send OTP via email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = email
            msg['Subject'] = "AstroSense Login Code"
            
            body = f"""
            Your AstroSense login code is: {otp}
            
            This code will expire in 5 minutes.
            
            If you didn't request this code, please ignore this email.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # For development, just log the OTP instead of sending email
            if not self.smtp_username:
                logger.info(f"OTP for {email}: {otp}")
                return True
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            text = msg.as_string()
            server.sendmail(self.from_email, email, text)
            server.quit()
            
            logger.info(f"OTP sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send OTP to {email}: {str(e)}")
            return False
    
    def request_otp(self, email: str) -> AuthResponse:
        """Request OTP for email"""
        try:
            # Generate OTP
            otp = self.generate_otp()
            otp_hash = self.hash_otp(otp)
            
            # Store OTP in database
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
            
            query = """
                INSERT INTO otps (email, otp_hash, expires_at, attempts)
                VALUES (%s, %s, %s, 0)
                ON CONFLICT (email) DO UPDATE
                SET otp_hash = EXCLUDED.otp_hash,
                    expires_at = EXCLUDED.expires_at,
                    attempts = 0,
                    created_at = CURRENT_TIMESTAMP
            """
            
            with self.db.get_cursor() as cursor:
                cursor.execute(query, (email, otp_hash, expires_at))
            
            # Send OTP via email
            if self.send_otp_email(email, otp):
                return AuthResponse(
                    success=True,
                    message=f"OTP sent to {email[:3]}***{email.split('@')[1]}"
                )
            else:
                return AuthResponse(
                    success=False,
                    message="Failed to send OTP. Please try again."
                )
                
        except Exception as e:
            logger.error(f"Error requesting OTP for {email}: {str(e)}")
            return AuthResponse(
                success=False,
                message="An error occurred. Please try again."
            )
    
    def verify_otp(self, email: str, otp: str) -> AuthResponse:
        """Verify OTP and create session"""
        try:
            # Get OTP from database
            query = """
                SELECT otp_hash, expires_at, attempts
                FROM otps
                WHERE email = %s
            """
            
            with self.db.get_cursor() as cursor:
                cursor.execute(query, (email,))
                result = cursor.fetchone()
                
                if not result:
                    return AuthResponse(
                        success=False,
                        message="Invalid or expired OTP"
                    )
                
                otp_hash = result['otp_hash']
                expires_at = result['expires_at']
                attempts = result['attempts']
                
                # Check if OTP is expired
                if datetime.now(timezone.utc) > expires_at:
                    return AuthResponse(
                        success=False,
                        message="OTP has expired. Please request a new one."
                    )
                
                # Check attempts limit
                if attempts >= 3:
                    return AuthResponse(
                        success=False,
                        message="Too many failed attempts. Please request a new OTP."
                    )
                
                # Verify OTP
                if not self.verify_otp_hash(otp, otp_hash):
                    # Increment attempts
                    cursor.execute(
                        "UPDATE otps SET attempts = attempts + 1 WHERE email = %s",
                        (email,)
                    )
                    return AuthResponse(
                        success=False,
                        message=f"Invalid OTP. {2 - attempts} attempts remaining."
                    )
                
                # OTP is valid, create or get user
                user = self.get_or_create_user(email)
                
                # Create session
                session_token = self.generate_session_token()
                expires_at = datetime.now(timezone.utc) + timedelta(days=7)
                
                session_query = """
                    INSERT INTO sessions (user_id, token, expires_at)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """
                
                cursor.execute(session_query, (user.id, session_token, expires_at))
                
                # Update user last login
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                    (user.id,)
                )
                
                # Delete used OTP
                cursor.execute("DELETE FROM otps WHERE email = %s", (email,))
                
                return AuthResponse(
                    success=True,
                    message="Login successful",
                    token=session_token,
                    user=user
                )
                
        except Exception as e:
            logger.error(f"Error verifying OTP for {email}: {str(e)}")
            return AuthResponse(
                success=False,
                message="An error occurred. Please try again."
            )
    
    def get_or_create_user(self, email: str) -> User:
        """Get existing user or create new one"""
        query = "SELECT id, email, created_at, last_login, is_active FROM users WHERE email = %s"
        
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (email,))
            result = cursor.fetchone()
            
            if result:
                return User(**result)
            
            # Create new user
            insert_query = """
                INSERT INTO users (email)
                VALUES (%s)
                RETURNING id, email, created_at, last_login, is_active
            """
            
            cursor.execute(insert_query, (email,))
            result = cursor.fetchone()
            
            return User(**result)
    
    def validate_session(self, token: str) -> Optional[User]:
        """Validate session token and return user"""
        try:
            query = """
                SELECT u.id, u.email, u.created_at, u.last_login, u.is_active
                FROM users u
                JOIN sessions s ON u.id = s.user_id
                WHERE s.token = %s AND s.expires_at > NOW() AND s.is_active = TRUE
            """
            
            with self.db.get_cursor() as cursor:
                cursor.execute(query, (token,))
                result = cursor.fetchone()
                
                if result:
                    # Update last accessed
                    cursor.execute(
                        "UPDATE sessions SET last_accessed = CURRENT_TIMESTAMP WHERE token = %s",
                        (token,)
                    )
                    return User(**result)
                
                return None
                
        except Exception as e:
            logger.error(f"Error validating session: {str(e)}")
            return None
    
    def logout(self, token: str) -> bool:
        """Logout user by invalidating session"""
        try:
            query = "UPDATE sessions SET is_active = FALSE WHERE token = %s"
            
            with self.db.get_cursor() as cursor:
                cursor.execute(query, (token,))
                return True
                
        except Exception as e:
            logger.error(f"Error logging out: {str(e)}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and OTPs"""
        try:
            with self.db.get_cursor() as cursor:
                # Delete expired sessions
                cursor.execute(
                    "DELETE FROM sessions WHERE expires_at < NOW() RETURNING id"
                )
                expired_sessions = len(cursor.fetchall())
                
                # Delete expired OTPs
                cursor.execute(
                    "DELETE FROM otps WHERE expires_at < NOW() RETURNING email"
                )
                expired_otps = len(cursor.fetchall())
                
                logger.info(f"Cleaned up {expired_sessions} sessions and {expired_otps} OTPs")
                return expired_sessions + expired_otps
                
        except Exception as e:
            logger.error(f"Error cleaning up expired data: {str(e)}")
            return 0


# Global auth service instance
auth_service = None

def get_auth_service() -> AuthService:
    """Get auth service instance"""
    global auth_service
    if auth_service is None:
        from database.manager import DatabaseManager
        db_manager = DatabaseManager()
        auth_service = AuthService(db_manager)
    return auth_service