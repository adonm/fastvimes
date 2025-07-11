"""Middleware for FastVimes."""

from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class IdentityMiddleware(BaseHTTPMiddleware):
    """Middleware to extract user identity from headers."""

    def __init__(
        self,
        app,
        user_id_header: str = "X-User-ID",
        user_role_header: str = "X-User-Role",
        **kwargs,
    ):
        super().__init__(app, **kwargs)
        self.user_id_header = user_id_header
        self.user_role_header = user_role_header

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Extract user identity from headers and add to request state."""
        # Extract user ID
        user_id = request.headers.get(self.user_id_header)
        request.state.user_id = user_id

        # Extract user role
        user_role = request.headers.get(self.user_role_header)
        request.state.user_role = user_role

        # Extract additional user headers
        for header_name, header_value in request.headers.items():
            if header_name.lower().startswith("x-user-"):
                # Convert header name to state attribute
                attr_name = (
                    header_name.lower().replace("x-user-", "user_").replace("-", "_")
                )
                setattr(request.state, attr_name, header_value)

        response = await call_next(request)
        return response


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to handle authentication."""

    def __init__(self, app, auth_header: str = "Authorization", **kwargs):
        super().__init__(app, **kwargs)
        self.auth_header = auth_header

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate authentication token."""
        # Extract token
        auth_value = request.headers.get(self.auth_header)

        # Validate token
        authenticated = self._validate_token(auth_value)
        request.state.authenticated = authenticated

        # Add token to state if valid
        if authenticated and auth_value:
            request.state.auth_token = auth_value

        response = await call_next(request)
        return response

    def _validate_token(self, token: str | None) -> bool:
        """Validate authentication token."""
        if not token:
            return False

        # Handle Bearer tokens
        if token.startswith("Bearer "):
            token = token[7:]  # Remove "Bearer " prefix
            if not token:
                return False

        # Simple token validation (implement your own logic)
        # This is a placeholder - replace with real validation
        valid_tokens = ["valid-token", "test-token", "valid-api-key"]
        return token in valid_tokens
