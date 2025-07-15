"""
Test Authlib authentication middleware.

Design Spec: AGENT.md - Security and Safety First - Authlib for authentication
Coverage: OAuth integration, JWT tokens, route protection, configuration
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from authlib.jose import jwt
from authlib.jose.errors import JoseError

from fastvimes.middleware.auth_authlib import (
    AuthMiddleware, 
    AuthUser, 
    AuthConfig, 
    setup_auth_routes,
    get_current_user,
    require_auth,
    require_admin
)
from fastvimes.config import FastVimesSettings


class TestAuthConfig:
    """
    Test authentication configuration.
    
    Design Spec: AGENT.md - Key Dependencies - Authlib Configuration
    Coverage: OAuth settings, JWT settings, authorization rules
    """
    
    def test_auth_config_defaults(self):
        """Test default authentication configuration."""
        config = AuthConfig()
        assert config.oauth_provider == "google"
        assert config.oauth_client_id == ""
        assert config.oauth_client_secret == ""
        assert config.oauth_redirect_uri == "http://localhost:8000/auth/callback"
        assert config.oauth_scopes == ["openid", "email", "profile"]
        assert config.jwt_algorithm == "HS256"
        assert config.jwt_expiration_minutes == 1440
        assert config.require_auth_for_read is False
        assert config.require_auth_for_write is True
        assert config.admin_users == []
    
    def test_auth_config_custom_values(self):
        """Test custom authentication configuration."""
        config = AuthConfig(
            oauth_provider="github",
            oauth_client_id="test-client-id",
            oauth_client_secret="test-client-secret",
            oauth_redirect_uri="https://example.com/callback",
            oauth_scopes=["read:user", "user:email"],
            jwt_secret_key="test-secret",
            jwt_algorithm="HS512",
            jwt_expiration_minutes=720,
            require_auth_for_read=True,
            require_auth_for_write=True,
            admin_users=["admin@example.com"]
        )
        assert config.oauth_provider == "github"
        assert config.oauth_client_id == "test-client-id"
        assert config.oauth_client_secret == "test-client-secret"
        assert config.oauth_redirect_uri == "https://example.com/callback"
        assert config.oauth_scopes == ["read:user", "user:email"]
        assert config.jwt_secret_key == "test-secret"
        assert config.jwt_algorithm == "HS512"
        assert config.jwt_expiration_minutes == 720
        assert config.require_auth_for_read is True
        assert config.require_auth_for_write is True
        assert config.admin_users == ["admin@example.com"]


class TestAuthUser:
    """
    Test authenticated user model.
    
    Design Spec: AGENT.md - Security and Safety First - User representation
    Coverage: User model validation, role management
    """
    
    def test_auth_user_creation(self):
        """Test AuthUser model creation."""
        user = AuthUser(
            id="123",
            email="test@example.com",
            name="Test User",
            roles=["user", "admin"]
        )
        assert user.id == "123"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.roles == ["user", "admin"]
    
    def test_auth_user_default_roles(self):
        """Test AuthUser with default roles."""
        user = AuthUser(
            id="123",
            email="test@example.com",
            name="Test User"
        )
        assert user.roles == []


class TestAuthMiddleware:
    """
    Test authentication middleware functionality.
    
    Design Spec: AGENT.md - Security and Safety First - Authentication middleware
    Coverage: Request processing, token validation, route protection
    """
    
    @pytest.fixture
    def auth_settings(self):
        """Create test authentication settings."""
        return FastVimesSettings(
            auth_enabled=True,
            auth_secret_key="test-secret-key",
            oauth_client_id="test-client-id",
            oauth_client_secret="test-client-secret",
            oauth_redirect_uri="http://localhost:8000/auth/callback",
            oauth_scopes=["openid", "email", "profile"],
            require_auth_for_read=False,
            require_auth_for_write=True,
            admin_users=["admin@example.com"]
        )
    
    @pytest.fixture
    def app_with_auth(self, auth_settings):
        """Create FastAPI app with auth middleware."""
        app = FastAPI()
        auth_middleware = AuthMiddleware(app, auth_settings)
        app.add_middleware(AuthMiddleware, settings=auth_settings)
        setup_auth_routes(app, auth_middleware)
        return app, auth_middleware
    
    def test_auth_middleware_initialization(self, auth_settings):
        """Test AuthMiddleware initialization."""
        app = FastAPI()
        middleware = AuthMiddleware(app, auth_settings)
        
        assert middleware.settings == auth_settings
        assert middleware.auth_config.oauth_client_id == "test-client-id"
        assert middleware.auth_config.oauth_client_secret == "test-client-secret"
        assert middleware.auth_config.require_auth_for_read is False
        assert middleware.auth_config.require_auth_for_write is True
        assert middleware.auth_config.admin_users == ["admin@example.com"]
    
    def test_get_metadata_url(self, auth_settings):
        """Test OAuth metadata URL generation."""
        app = FastAPI()
        middleware = AuthMiddleware(app, auth_settings)
        
        # Test Google metadata URL
        url = middleware._get_metadata_url()
        assert url == "https://accounts.google.com/.well-known/openid-configuration"
        
        # Test GitHub metadata URL
        middleware.auth_config.oauth_provider = "github"
        url = middleware._get_metadata_url()
        assert url == "https://github.com/.well-known/openid-configuration"
        
        # Test Microsoft metadata URL
        middleware.auth_config.oauth_provider = "microsoft"
        url = middleware._get_metadata_url()
        assert url == "https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration"
    
    def test_create_jwt_token(self, auth_settings):
        """Test JWT token creation."""
        app = FastAPI()
        middleware = AuthMiddleware(app, auth_settings)
        
        user_data = {
            'id': '123',
            'email': 'test@example.com',
            'name': 'Test User',
            'roles': ['user']
        }
        
        with patch('time.time', return_value=1000000):
            token = middleware.create_jwt_token(user_data)
            
            # Verify token can be decoded
            payload = jwt.decode(token, auth_settings.auth_secret_key)
            assert payload['sub'] == '123'
            assert payload['email'] == 'test@example.com'
            assert payload['name'] == 'Test User'
            assert payload['roles'] == ['user']
            assert payload['iat'] == 1000000
            assert payload['exp'] == 1000000 + (1440 * 60)  # 24 hours
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, auth_settings):
        """Test getting current user with valid token."""
        app = FastAPI()
        middleware = AuthMiddleware(app, auth_settings)
        
        # Create valid token
        user_data = {
            'id': '123',
            'email': 'test@example.com',
            'name': 'Test User',
            'roles': ['user']
        }
        
        with patch('time.time', return_value=1000000):
            token = middleware.create_jwt_token(user_data)
        
        # Mock request with valid token
        request = Mock()
        request.headers = {'Authorization': f'Bearer {token}'}
        
        user = await middleware._get_current_user(request)
        assert user is not None
        assert user.id == '123'
        assert user.email == 'test@example.com'
        assert user.name == 'Test User'
        assert user.roles == ['user']
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, auth_settings):
        """Test getting current user with invalid token."""
        app = FastAPI()
        middleware = AuthMiddleware(app, auth_settings)
        
        # Mock request with invalid token
        request = Mock()
        request.headers = {'Authorization': 'Bearer invalid-token'}
        
        user = await middleware._get_current_user(request)
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, auth_settings):
        """Test getting current user with no token."""
        app = FastAPI()
        middleware = AuthMiddleware(app, auth_settings)
        
        # Mock request with no token
        request = Mock()
        request.headers = {}
        
        user = await middleware._get_current_user(request)
        assert user is None


class TestAuthRoutes:
    """
    Test authentication routes.
    
    Design Spec: AGENT.md - Security and Safety First - OAuth flow
    Coverage: Login, callback, logout, user info endpoints
    """
    
    @pytest.fixture
    def client_with_auth(self, auth_settings):
        """Create test client with auth middleware."""
        app = FastAPI()
        auth_middleware = AuthMiddleware(app, auth_settings)
        setup_auth_routes(app, auth_middleware)
        return TestClient(app), auth_middleware
    
    def test_login_route_exists(self, client_with_auth):
        """Test login route exists and redirects."""
        client, middleware = client_with_auth
        
        with patch.object(middleware.oauth, 'create_client') as mock_create_client:
            mock_client = Mock()
            mock_client.authorize_redirect = AsyncMock()
            mock_create_client.return_value = mock_client
            
            response = client.get("/auth/login")
            # Should attempt to redirect to OAuth provider
            mock_create_client.assert_called_once()
    
    def test_logout_route(self, client_with_auth):
        """Test logout route."""
        client, middleware = client_with_auth
        
        response = client.post("/auth/logout")
        assert response.status_code == 200
        # Should redirect and clear cookies
        assert response.url.path == "/"
    
    def test_me_route_no_auth(self, client_with_auth):
        """Test /auth/me route without authentication."""
        client, middleware = client_with_auth
        
        response = client.get("/auth/me")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
    
    def test_me_route_with_auth(self, client_with_auth, auth_settings):
        """Test /auth/me route with authentication."""
        client, middleware = client_with_auth
        
        # Create valid token
        user_data = {
            'id': '123',
            'email': 'test@example.com',
            'name': 'Test User',
            'roles': ['user']
        }
        
        with patch('time.time', return_value=1000000):
            token = middleware.create_jwt_token(user_data)
        
        # Make request with valid token
        headers = {'Authorization': f'Bearer {token}'}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == '123'
        assert data['email'] == 'test@example.com'
        assert data['name'] == 'Test User'
        assert data['roles'] == ['user']


class TestAuthDependencies:
    """
    Test authentication dependencies.
    
    Design Spec: AGENT.md - Security and Safety First - Route protection
    Coverage: Authentication requirements, admin privileges
    """
    
    def test_get_current_user_dependency(self):
        """Test get_current_user dependency."""
        # Mock request with user in state
        request = Mock()
        user = AuthUser(id="123", email="test@example.com", name="Test User")
        request.state = Mock()
        request.state.user = user
        
        result = get_current_user(request)
        assert result == user
    
    def test_get_current_user_dependency_no_user(self):
        """Test get_current_user dependency with no user."""
        request = Mock()
        request.state = Mock()
        
        result = get_current_user(request)
        assert result is None
    
    def test_require_auth_dependency(self):
        """Test require_auth dependency with authenticated user."""
        request = Mock()
        user = AuthUser(id="123", email="test@example.com", name="Test User")
        request.state = Mock()
        request.state.user = user
        
        result = require_auth(request)
        assert result == user
    
    def test_require_auth_dependency_no_user(self):
        """Test require_auth dependency without authentication."""
        request = Mock()
        request.state = Mock()
        
        with pytest.raises(Exception) as exc_info:
            require_auth(request)
        assert "Authentication required" in str(exc_info.value)
    
    def test_require_admin_dependency(self):
        """Test require_admin dependency with admin user."""
        request = Mock()
        user = AuthUser(id="123", email="admin@example.com", name="Admin User")
        request.state = Mock()
        request.state.user = user
        
        auth_config = AuthConfig(admin_users=["admin@example.com"])
        result = require_admin(request, auth_config)
        assert result == user
    
    def test_require_admin_dependency_non_admin(self):
        """Test require_admin dependency with non-admin user."""
        request = Mock()
        user = AuthUser(id="123", email="user@example.com", name="Regular User")
        request.state = Mock()
        request.state.user = user
        
        auth_config = AuthConfig(admin_users=["admin@example.com"])
        with pytest.raises(Exception) as exc_info:
            require_admin(request, auth_config)
        assert "Admin privileges required" in str(exc_info.value)


class TestAuthIntegration:
    """
    Test authentication integration with FastAPI.
    
    Design Spec: AGENT.md - Security and Safety First - Complete auth flow
    Coverage: Middleware integration, request processing, error handling
    """
    
    @pytest.fixture
    def protected_app(self, auth_settings):
        """Create app with protected routes."""
        app = FastAPI()
        
        @app.get("/public")
        def public_endpoint():
            return {"message": "public"}
        
        @app.get("/protected")
        def protected_endpoint(user: AuthUser = Depends(require_auth)):
            return {"message": f"Hello {user.name}"}
        
        @app.post("/write")
        def write_endpoint(user: AuthUser = Depends(require_auth)):
            return {"message": "write operation"}
        
        auth_middleware = AuthMiddleware(app, auth_settings)
        setup_auth_routes(app, auth_middleware)
        return TestClient(app), auth_middleware
    
    def test_public_endpoint_no_auth(self, protected_app):
        """Test public endpoint without authentication."""
        client, middleware = protected_app
        
        response = client.get("/public")
        assert response.status_code == 200
        assert response.json() == {"message": "public"}
    
    def test_protected_endpoint_no_auth(self, protected_app):
        """Test protected endpoint without authentication."""
        client, middleware = protected_app
        
        response = client.get("/protected")
        assert response.status_code == 401
    
    def test_protected_endpoint_with_auth(self, protected_app, auth_settings):
        """Test protected endpoint with authentication."""
        client, middleware = protected_app
        
        # Create valid token
        user_data = {
            'id': '123',
            'email': 'test@example.com',
            'name': 'Test User',
            'roles': ['user']
        }
        
        with patch('time.time', return_value=1000000):
            token = middleware.create_jwt_token(user_data)
        
        headers = {'Authorization': f'Bearer {token}'}
        response = client.get("/protected", headers=headers)
        
        assert response.status_code == 200
        assert response.json() == {"message": "Hello Test User"}
    
    def test_write_endpoint_with_auth(self, protected_app, auth_settings):
        """Test write endpoint with authentication."""
        client, middleware = protected_app
        
        # Create valid token
        user_data = {
            'id': '123',
            'email': 'test@example.com',
            'name': 'Test User',
            'roles': ['user']
        }
        
        with patch('time.time', return_value=1000000):
            token = middleware.create_jwt_token(user_data)
        
        headers = {'Authorization': f'Bearer {token}'}
        response = client.post("/write", headers=headers)
        
        assert response.status_code == 200
        assert response.json() == {"message": "write operation"}
