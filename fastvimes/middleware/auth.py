"""Authentication middleware for FastVimes."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from nicegui import ui
import jwt

from ..config import FastVimesSettings


class AuthenticationManager:
    """Manages authentication for FastVimes."""
    
    def __init__(self, settings: FastVimesSettings):
        """Initialize authentication manager."""
        self.settings = settings
        self.secret_key = settings.auth_secret_key or secrets.token_hex(32)
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.auth_token_expire_minutes
        
        # Simple in-memory user store (in production, use proper database)
        self.users = {
            "admin": {
                "username": "admin",
                "password_hash": self._hash_password("admin123"),
                "role": "admin",
                "active": True
            },
            "user": {
                "username": "user",
                "password_hash": self._hash_password("user123"),
                "role": "user",
                "active": True
            }
        }
        
        # Active sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
        
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        return self._hash_password(password) == password_hash
        
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username/password."""
        user = self.users.get(username)
        if not user or not user.get("active"):
            return None
            
        if not self.verify_password(password, user["password_hash"]):
            return None
            
        return user
        
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT access token."""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode = {
            "sub": user_data["username"],
            "role": user_data["role"],
            "exp": expire
        }
        
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        # Store in active sessions
        self.active_sessions[token] = {
            "username": user_data["username"],
            "role": user_data["role"],
            "created_at": datetime.utcnow(),
            "expires_at": expire
        }
        
        return token
        
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user data."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            role: str = payload.get("role")
            
            if username is None:
                return None
                
            # Check if session is still active
            if token not in self.active_sessions:
                return None
                
            session = self.active_sessions[token]
            if session["expires_at"] < datetime.utcnow():
                # Remove expired session
                del self.active_sessions[token]
                return None
                
            return {
                "username": username,
                "role": role,
                "token": token
            }
            
        except jwt.PyJWTError:
            return None
            
    def logout_user(self, token: str) -> bool:
        """Logout user by removing session."""
        if token in self.active_sessions:
            del self.active_sessions[token]
            return True
        return False
        
    def require_role(self, required_role: str = "user"):
        """Decorator to require specific role."""
        def decorator(user_data: Dict[str, Any] = Depends(self.get_current_user)):
            if not user_data:
                raise HTTPException(status_code=401, detail="Authentication required")
                
            user_role = user_data.get("role")
            if required_role == "admin" and user_role != "admin":
                raise HTTPException(status_code=403, detail="Admin access required")
                
            return user_data
        return decorator
        
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """Get current user from token."""
        token = credentials.credentials
        user_data = self.verify_token(token)
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
            
        return user_data


class AuthenticationUI:
    """UI components for authentication."""
    
    def __init__(self, auth_manager: AuthenticationManager):
        """Initialize authentication UI."""
        self.auth_manager = auth_manager
        
    def render_login_page(self):
        """Render login page."""
        with ui.card().classes('w-full max-w-md mx-auto mt-16'):
            ui.label('FastVimes Login').classes('text-h4 text-center mb-6')
            
            with ui.column().classes('w-full gap-4'):
                username_input = ui.input('Username', placeholder='Enter username').classes('w-full')
                password_input = ui.input('Password', placeholder='Enter password', password=True).classes('w-full')
                
                with ui.row().classes('w-full justify-center'):
                    ui.button('Login', on_click=lambda: self._handle_login(username_input, password_input)).props('color=primary')
                    
                # Demo credentials info
                with ui.expansion('Demo Credentials', icon='info'):
                    ui.label('Admin: admin / admin123').classes('text-sm')
                    ui.label('User: user / user123').classes('text-sm')
                    
    def _handle_login(self, username_input, password_input):
        """Handle login form submission."""
        username = username_input.value
        password = password_input.value
        
        if not username or not password:
            ui.notify('Please enter username and password', type='negative')
            return
            
        user = self.auth_manager.authenticate_user(username, password)
        if not user:
            ui.notify('Invalid username or password', type='negative')
            return
            
        # Create access token
        token = self.auth_manager.create_access_token(user)
        
        # Store token in browser storage
        ui.run_javascript(f'localStorage.setItem("fastvimes_token", "{token}")')
        
        # Redirect to main page
        ui.notify(f'Welcome, {username}!', type='positive')
        ui.navigate.to('/')
        
    def render_logout_button(self):
        """Render logout button."""
        ui.button('Logout', icon='logout', on_click=self._handle_logout).props('flat')
        
    def _handle_logout(self):
        """Handle logout."""
        # Get token from browser storage
        ui.run_javascript('''
            const token = localStorage.getItem("fastvimes_token");
            if (token) {
                localStorage.removeItem("fastvimes_token");
                window.location.href = "/login";
            }
        ''')
        
    def render_user_info(self, user_data: Dict[str, Any]):
        """Render user information."""
        with ui.row().classes('items-center gap-2'):
            ui.avatar(user_data['username'][0].upper()).props('size=sm')
            ui.label(f"{user_data['username']} ({user_data['role']})").classes('text-sm')
            self.render_logout_button()
            
    def check_authentication(self) -> Optional[Dict[str, Any]]:
        """Check if user is authenticated."""
        # This would typically get token from browser storage
        # For demo purposes, we'll return a mock user
        return {
            "username": "demo_user",
            "role": "admin",
            "token": "demo_token"
        }


def create_auth_middleware(settings: FastVimesSettings):
    """Create authentication middleware."""
    auth_manager = AuthenticationManager(settings)
    auth_ui = AuthenticationUI(auth_manager)
    
    return auth_manager, auth_ui


def require_auth(auth_manager: AuthenticationManager):
    """Dependency to require authentication."""
    def dependency(request: Request):
        """Check authentication for request."""
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Authentication required")
            
        token = auth_header.split(' ')[1]
        user_data = auth_manager.verify_token(token)
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
            
        return user_data
    return dependency


def require_admin(auth_manager: AuthenticationManager):
    """Dependency to require admin role."""
    def dependency(user_data: Dict[str, Any] = Depends(require_auth(auth_manager))):
        """Check admin role for request."""
        if user_data.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        return user_data
    return dependency
