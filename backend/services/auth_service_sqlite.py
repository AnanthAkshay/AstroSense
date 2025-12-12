"""
Authentication Service for AstroSense (SQLite version)
Simple email OTP authentication using SQLite
"""
import secrets
import hashlib
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import os
import logging

from database.sqlite_manager import SQLiteManager
from models.auth import User, Session, OTP, AuthResponse

logger = logging.getLogger(__name__)


class AuthServiceSQLite:
    """Simple authentication service with email OTP using SQLite"""
    
    def __init__(self, db_manager: SQLiteManager):
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
        """Send OTP via email using synchronous Gmail SMTP"""
        try:
            # Import here to avoid circular imports
            from utils.simple_emailer import send_otp_email_sync
            
            # Attempt to send email
            success, message = send_otp_email_sync(email, otp)
            
            if success:
                logger.info(f"✅ {message}")
                return True
            else:
                logger.warning(f"📧 Email delivery failed: {message}")
                # SECURITY: Do NOT log OTP in production
                # For development only - remove in production
                if os.getenv('ENVIRONMENT', 'development') == 'development':
                    masked_email = f"{email[:3]}***{email.split('@')[1]}"
                    print(f"\n🔐 DEV FALLBACK - Check console for OTP sent to {masked_email}")
                    print(f"OTP: {otp}")
                    print("📧 Configure SMTP in .env for real email delivery\n")
                return True  # Return True so auth flow continues
                
        except Exception as e:
            logger.error(f"❌ Email service error: {str(e)}")
            # SECURITY: Do NOT log OTP in production
            if os.getenv('ENVIRONMENT', 'development') == 'development':
                masked_email = f"{email[:3]}***{email.split('@')[1]}"
                print(f"\n🔐 DEV FALLBACK - Email error for {masked_email}")
                print(f"OTP: {otp}")
                print("📧 Fix SMTP configuration for email delivery\n")
            return True  # Return True so auth flow continues
    
    def request_otp(self, email: str, is_resend: bool = False) -> AuthResponse:
        """Request OTP for email with resend tracking"""
        try:
            # Check existing OTP for resend limits
            resend_count = 0
            if is_resend:
                with self.db.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT attempts FROM otps WHERE email = ? AND expires_at > CURRENT_TIMESTAMP
                    """, (email,))
                    result = cursor.fetchone()
                    if result:
                        resend_count = result['attempts']
                        if resend_count >= 2:  # Maximum 2 resends
                            return AuthResponse(
                                success=False,
                                message="Maximum resend limit reached. Please try again later."
                            )
            
            # Generate new OTP
            otp = self.generate_otp()
            otp_hash = self.hash_otp(otp)
            
            # Store OTP in database with resend count
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
            new_resend_count = resend_count + 1 if is_resend else 0
            
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT OR REPLACE INTO otps (email, otp_hash, expires_at, attempts, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (email, otp_hash, expires_at.isoformat(), new_resend_count))
            
            # Send OTP via email
            if self.send_otp_email(email, otp):
                masked_email = f"{email[:3]}***{email.split('@')[1]}"
                resend_info = f" (Resend {new_resend_count}/2)" if is_resend else ""
                return AuthResponse(
                    success=True,
                    message=f"Code sent to {masked_email}{resend_info}"
                )
            else:
                return AuthResponse(
                    success=False,
                    message="Failed to send code. Please try again."
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
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT otp_hash, expires_at, attempts
                    FROM otps
                    WHERE email = ?
                """, (email,))
                
                result = cursor.fetchone()
                
                if not result:
                    return AuthResponse(
                        success=False,
                        message="Code not found. Please request a new code."
                    )
                
                otp_hash = result['otp_hash']
                expires_at_str = result['expires_at']
                verification_attempts = result['attempts']
                
                # Parse expires_at
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                
                # Check if OTP is expired
                if datetime.now(timezone.utc) > expires_at:
                    return AuthResponse(
                        success=False,
                        message="Code has expired. Please request a new code."
                    )
                
                # Verify OTP
                if not self.verify_otp_hash(otp, otp_hash):
                    return AuthResponse(
                        success=False,
                        message="Wrong code entered. Please check and try again."
                    )
                
                # OTP is valid, create or get user
                user = self.get_or_create_user(email)
                
                # Create session
                session_token = self.generate_session_token()
                expires_at = datetime.now(timezone.utc) + timedelta(days=7)
                
                cursor.execute("""
                    INSERT INTO sessions (user_id, token, expires_at)
                    VALUES (?, ?, ?)
                """, (user.id, session_token, expires_at.isoformat()))
                
                # Update user last login
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                    (user.id,)
                )
                
                # Delete used OTP
                cursor.execute("DELETE FROM otps WHERE email = ?", (email,))
                
                # Convert user to dict for JSON serialization
                user_dict = {
                    "id": user.id,
                    "email": user.email,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "is_active": user.is_active
                }
                
                return AuthResponse(
                    success=True,
                    message="Login successful! Welcome to AstroSense.",
                    token=session_token,
                    user=user_dict
                )
                
        except Exception as e:
            logger.error(f"Error verifying OTP for {email}: {str(e)}")
            return AuthResponse(
                success=False,
                message="An error occurred. Please try again."
            )
    
    def get_or_create_user(self, email: str) -> User:
        """Get existing user or create new one"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, email, created_at, last_login, is_active 
                FROM users WHERE email = ?
            """, (email,))
            
            result = cursor.fetchone()
            
            if result:
                return User(
                    id=result['id'],
                    email=result['email'],
                    created_at=result['created_at'],
                    last_login=result['last_login'],
                    is_active=bool(result['is_active'])
                )
            
            # Create new user
            cursor.execute("""
                INSERT INTO users (email)
                VALUES (?)
            """, (email,))
            
            user_id = cursor.lastrowid
            
            cursor.execute("""
                SELECT id, email, created_at, last_login, is_active 
                FROM users WHERE id = ?
            """, (user_id,))
            
            result = cursor.fetchone()
            
            return User(
                id=result['id'],
                email=result['email'],
                created_at=result['created_at'],
                last_login=result['last_login'],
                is_active=bool(result['is_active'])
            )
    
    def validate_session(self, token: str) -> Optional[User]:
        """Validate session token and return user"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT u.id, u.email, u.created_at, u.last_login, u.is_active
                    FROM users u
                    JOIN sessions s ON u.id = s.user_id
                    WHERE s.token = ? AND s.expires_at > CURRENT_TIMESTAMP AND s.is_active = 1
                """, (token,))
                
                result = cursor.fetchone()
                
                if result:
                    # Update last accessed
                    cursor.execute(
                        "UPDATE sessions SET last_accessed = CURRENT_TIMESTAMP WHERE token = ?",
                        (token,)
                    )
                    
                    return User(
                        id=result['id'],
                        email=result['email'],
                        created_at=result['created_at'],
                        last_login=result['last_login'],
                        is_active=bool(result['is_active'])
                    )
                
                return None
                
        except Exception as e:
            logger.error(f"Error validating session: {str(e)}")
            return None
    
    def logout(self, token: str) -> bool:
        """Logout user by invalidating session"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("UPDATE sessions SET is_active = 0 WHERE token = ?", (token,))
                return True
                
        except Exception as e:
            logger.error(f"Error logging out: {str(e)}")
            return False


# Global auth service instance
auth_service_sqlite = None

def get_auth_service_sqlite() -> AuthServiceSQLite:
    """Get SQLite auth service instance"""
    global auth_service_sqlite
    if auth_service_sqlite is None:
        from database.sqlite_manager import get_sqlite_manager
        db_manager = get_sqlite_manager()
        auth_service_sqlite = AuthServiceSQLite(db_manager)
    return auth_service_sqlite