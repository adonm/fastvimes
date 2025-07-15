"""Authentication middleware using Authlib for FastAPI."""

import secrets
import time
from typing import Any

from authlib.integrations.starlette_client import OAuth, OAuthError
from authlib.jose import jwt
from authlib.jose.errors import JoseError
from fastapi import FastAPI, HTTPException, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import RedirectResponse, Response

from ..config import FastVimesSettings


class AuthUser(BaseModel):
    """Authenticated user model."""

    id: str
    email: str
    name: str
    roles: list[str] = []


class AuthConfig(BaseModel):
    """Authentication configuration."""

    # OAuth Configuration
    oauth_provider: str = "google"  # google, github, microsoft, etc.
    oauth_client_id: str = ""
    oauth_client_secret: str = ""
    oauth_redirect_uri: str = "http://localhost:8000/auth/callback"
    oauth_scopes: list[str] = ["openid", "email", "profile"]

    # JWT Configuration
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440  # 24 hours

    # Authorization Configuration
    require_auth_for_read: bool = False
    require_auth_for_write: bool = True
    admin_users: list[str] = []


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware using Authlib for OAuth/OpenID Connect."""

    def __init__(self, app: FastAPI, settings: FastVimesSettings):
        super().__init__(app)
        self.settings = settings
        self.auth_config = AuthConfig(
            oauth_client_id=settings.oauth_client_id,
            oauth_client_secret=settings.oauth_client_secret,
            oauth_redirect_uri=settings.oauth_redirect_uri,
            oauth_scopes=settings.oauth_scopes,
            jwt_secret_key=settings.auth_secret_key or secrets.token_urlsafe(32),
            require_auth_for_read=settings.require_auth_for_read,
            require_auth_for_write=settings.require_auth_for_write,
            admin_users=settings.admin_users,
        )

        # Initialize OAuth client
        self.oauth = OAuth()
        self.oauth.register(
            name=self.auth_config.oauth_provider,
            client_id=self.auth_config.oauth_client_id,
            client_secret=self.auth_config.oauth_client_secret,
            server_metadata_url=self._get_metadata_url(),
            client_kwargs={"scope": " ".join(self.auth_config.oauth_scopes)},
        )

        # HTTP Bearer token handler
        self.bearer = HTTPBearer(auto_error=False)

    def _get_metadata_url(self) -> str:
        """Get OAuth metadata URL based on provider."""
        metadata_urls = {
            "google": "https://accounts.google.com/.well-known/openid-configuration",
            "github": "https://github.com/.well-known/openid-configuration",
            "microsoft": "https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration",
        }
        return metadata_urls.get(self.auth_config.oauth_provider, "")

    async def dispatch(self, request: StarletteRequest, call_next) -> Response:
        """Process request through authentication middleware."""
        # Skip authentication for auth endpoints
        if request.url.path.startswith("/auth/"):
            return await call_next(request)

        # Skip authentication for public endpoints if not required
        if not self.auth_config.require_auth_for_read and request.method == "GET":
            return await call_next(request)

        # Check for authentication on write operations
        if self.auth_config.require_auth_for_write and request.method in [
            "POST",
            "PUT",
            "DELETE",
        ]:
            user = await self._get_current_user(request)
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            request.state.user = user

        return await call_next(request)

    async def _get_current_user(self, request: StarletteRequest) -> AuthUser | None:
        """Get current authenticated user from request."""
        # Try to get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1]

        try:
            payload = jwt.decode(token, self.auth_config.jwt_secret_key)
            return AuthUser(
                id=payload.get("sub", ""),
                email=payload.get("email", ""),
                name=payload.get("name", ""),
                roles=payload.get("roles", []),
            )
        except JoseError:
            return None

    def create_jwt_token(self, user_data: dict[str, Any]) -> str:
        """Create JWT token for authenticated user."""
        payload = {
            "sub": user_data.get("id", ""),
            "email": user_data.get("email", ""),
            "name": user_data.get("name", ""),
            "roles": user_data.get("roles", []),
            "iat": int(time.time()),
            "exp": int(time.time()) + (self.auth_config.jwt_expiration_minutes * 60),
        }
        return jwt.encode(
            {"alg": self.auth_config.jwt_algorithm},
            payload,
            self.auth_config.jwt_secret_key,
        )


def setup_auth_routes(app: FastAPI, auth_middleware: AuthMiddleware):
    """Setup authentication routes for OAuth flow."""

    @app.get("/auth/login")
    async def login(request: Request):
        """Initiate OAuth login flow."""
        client = auth_middleware.oauth.create_client(
            auth_middleware.auth_config.oauth_provider
        )
        redirect_uri = auth_middleware.auth_config.oauth_redirect_uri
        return await client.authorize_redirect(request, redirect_uri)

    @app.get("/auth/callback")
    async def callback(request: Request):
        """Handle OAuth callback."""
        client = auth_middleware.oauth.create_client(
            auth_middleware.auth_config.oauth_provider
        )

        try:
            token = await client.authorize_access_token(request)
            user_info = await client.get_user_info(token)

            # Create JWT token
            jwt_token = auth_middleware.create_jwt_token(
                {
                    "id": user_info.get("sub"),
                    "email": user_info.get("email"),
                    "name": user_info.get("name"),
                    "roles": ["user"],  # Default role, can be enhanced
                }
            )

            # Return token or redirect to frontend with token
            response = RedirectResponse(url="/")
            response.set_cookie(
                key="access_token",
                value=jwt_token,
                httponly=True,
                secure=True,
                samesite="lax",
            )
            return response

        except OAuthError as e:
            raise HTTPException(status_code=400, detail=f"OAuth error: {e}")

    @app.post("/auth/logout")
    async def logout():
        """Logout user."""
        response = RedirectResponse(url="/")
        response.delete_cookie("access_token")
        return response

    @app.get("/auth/me")
    async def get_current_user(request: Request):
        """Get current authenticated user."""
        user = await auth_middleware._get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return user


def get_current_user(request: Request) -> AuthUser | None:
    """Dependency to get current user from request state."""
    return getattr(request.state, "user", None)


def require_auth(request: Request) -> AuthUser:
    """Dependency that requires authentication."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_admin(request: Request, auth_config: AuthConfig) -> AuthUser:
    """Dependency that requires admin privileges."""
    user = require_auth(request)
    if user.email not in auth_config.admin_users:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user
