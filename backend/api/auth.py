"""
Authentication API endpoints for AstroSense
"""
from fastapi import APIRouter, HTTPException, Depends, status, Cookie
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from models.auth import LoginRequest, VerifyOTPRequest, AuthResponse, User
from services.auth_service_sqlite import get_auth_service_sqlite, AuthServiceSQLite

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/auth", tags=["authentication"])


def get_current_user(
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    auth_service: AuthServiceSQLite = Depends(get_auth_service_sqlite)
) -> Optional[User]:
    """Get current authenticated user from session token"""
    if not session_token:
        return None
    
    user = auth_service.validate_session(session_token)
    return user


@router.post("/login")
async def login(
    request: LoginRequest,
    auth_service: AuthServiceSQLite = Depends(get_auth_service_sqlite)
) -> AuthResponse:
    """
    POST /api/auth/login
    
    Request OTP for email address
    """
    try:
        logger.info(f"Login request for email: {request.email}")
        
        response = auth_service.request_otp(request.email, is_resend=False)
        
        if response.success:
            logger.info(f"OTP sent successfully to {request.email}")
        else:
            logger.warning(f"Failed to send OTP to {request.email}: {response.message}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in login endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )


@router.post("/resend")
async def resend_otp(
    request: LoginRequest,
    auth_service: AuthServiceSQLite = Depends(get_auth_service_sqlite)
) -> AuthResponse:
    """
    POST /api/auth/resend
    
    Resend OTP for email address (max 2 times)
    """
    try:
        logger.info(f"Resend OTP request for email: {request.email}")
        
        response = auth_service.request_otp(request.email, is_resend=True)
        
        if response.success:
            logger.info(f"OTP resent successfully to {request.email}")
        else:
            logger.warning(f"Failed to resend OTP to {request.email}: {response.message}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in resend endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during resend"
        )


@router.post("/verify")
async def verify_otp(
    request: VerifyOTPRequest,
    auth_service: AuthServiceSQLite = Depends(get_auth_service_sqlite)
) -> JSONResponse:
    """
    POST /api/auth/verify
    
    Verify OTP and create session
    """
    try:
        logger.info(f"OTP verification request for email: {request.email}")
        
        response = auth_service.verify_otp(request.email, request.otp)
        
        if response.success:
            logger.info(f"OTP verification successful for {request.email}")
            
            # Create response with session cookie
            json_response = JSONResponse(
                content={
                    "success": True,
                    "message": response.message,
                    "user": response.user if response.user else None
                }
            )
            
            # Set secure session cookie
            json_response.set_cookie(
                key="session_token",
                value=response.token,
                max_age=7 * 24 * 60 * 60,  # 7 days
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite="lax"
            )
            
            return json_response
        else:
            logger.warning(f"OTP verification failed for {request.email}: {response.message}")
            return JSONResponse(
                content={
                    "success": False,
                    "message": response.message
                },
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
    except Exception as e:
        logger.error(f"Error in verify endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during verification"
        )


@router.get("/me")
async def get_current_user_info(
    current_user: Optional[User] = Depends(get_current_user)
) -> dict:
    """
    GET /api/auth/me
    
    Get current authenticated user info
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return {
        "user": current_user.dict(),
        "authenticated": True
    }


@router.post("/logout")
async def logout(
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    auth_service: AuthServiceSQLite = Depends(get_auth_service_sqlite)
) -> JSONResponse:
    """
    POST /api/auth/logout
    
    Logout user and invalidate session
    """
    try:
        if session_token:
            auth_service.logout(session_token)
            logger.info("User logged out successfully")
        
        # Create response and clear session cookie
        json_response = JSONResponse(
            content={
                "success": True,
                "message": "Logged out successfully"
            }
        )
        
        json_response.delete_cookie(
            key="session_token",
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        return json_response
        
    except Exception as e:
        logger.error(f"Error in logout endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout"
        )


@router.get("/status")
async def auth_status(
    current_user: Optional[User] = Depends(get_current_user)
) -> dict:
    """
    GET /api/auth/status
    
    Check authentication status
    """
    return {
        "authenticated": current_user is not None,
        "user": current_user.dict() if current_user else None
    }