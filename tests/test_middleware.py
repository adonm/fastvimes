"""Test middleware functionality."""

from fastapi import Request
from fastapi.testclient import TestClient

from fastvimes.app import FastVimes


class TestMiddleware:
    """Test middleware functionality."""

    def test_identity_middleware_setup(self):
        """Test that middleware can be added to FastVimes."""
        app = FastVimes(db_path=":memory:")

        # Add custom middleware
        @app.middleware("http")
        async def test_middleware(request: Request, call_next):
            response = await call_next(request)
            response.headers["X-Test"] = "middleware-works"
            return response

        client = TestClient(app)
        response = client.get("/docs")

        # Should have our custom header
        assert response.headers.get("X-Test") == "middleware-works"

    def test_identity_header_processing(self):
        """Test processing of identity headers."""
        app = FastVimes(db_path=":memory:")

        # Create test table
        app.connection.raw_sql("CREATE TABLE test_table (id INTEGER)")

        # Add identity middleware
        @app.middleware("http")
        async def identity_middleware(request: Request, call_next):
            # Extract identity headers
            user_id = request.headers.get("X-User-ID")
            role = request.headers.get("X-User-Role")

            # Store in request state
            request.state.user_id = user_id
            request.state.role = role

            response = await call_next(request)
            return response

        # Add test endpoint that won't conflict with dynamic routes
        @app.get("/api/test-identity")
        async def test_identity(request: Request):
            return {
                "user_id": getattr(request.state, "user_id", None),
                "role": getattr(request.state, "role", None),
            }

        client = TestClient(app)

        # Test with identity headers
        response = client.get(
            "/api/test-identity", headers={"X-User-ID": "123", "X-User-Role": "admin"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "123"
        assert data["role"] == "admin"

    def test_request_logging_middleware(self):
        """Test request logging middleware."""
        app = FastVimes(db_path=":memory:")

        # Track requests
        requests_log = []

        @app.middleware("http")
        async def logging_middleware(request: Request, call_next):
            requests_log.append(
                {
                    "method": request.method,
                    "url": str(request.url),
                    "headers": dict(request.headers),
                }
            )

            response = await call_next(request)
            return response

        client = TestClient(app)

        # Make request
        client.get("/docs")

        # Check logging
        assert len(requests_log) == 1
        assert requests_log[0]["method"] == "GET"
        assert "/docs" in requests_log[0]["url"]

    def test_error_handling_middleware(self):
        """Test error handling middleware."""
        app = FastVimes(db_path=":memory:")

        # Create test table
        app.connection.raw_sql("CREATE TABLE test_table (id INTEGER)")

        # Add error handling middleware
        @app.middleware("http")
        async def error_handler(request: Request, call_next):
            try:
                response = await call_next(request)
                return response
            except Exception as e:
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=500,
                    content={"error": "Internal server error", "detail": str(e)},
                )

        # Add endpoint that raises error (using api/ prefix to avoid conflicts)
        @app.get("/api/error")
        async def error_endpoint():
            raise ValueError("Test error")

        client = TestClient(app)

        # Test error handling
        response = client.get("/api/error")
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "Internal server error"
        assert "Test error" in data["detail"]

    def test_rate_limiting_middleware(self):
        """Test rate limiting middleware concept."""
        app = FastVimes(db_path=":memory:")

        # Simple rate limiting
        request_counts = {}

        @app.middleware("http")
        async def rate_limiter(request: Request, call_next):
            client_ip = request.client.host

            # Count requests
            request_counts[client_ip] = request_counts.get(client_ip, 0) + 1

            # Simple limit
            if request_counts[client_ip] > 100:
                from fastapi import HTTPException

                raise HTTPException(status_code=429, detail="Rate limit exceeded")

            response = await call_next(request)
            return response

        client = TestClient(app)

        # Test that requests work normally
        response = client.get("/docs")
        assert response.status_code == 200

        # Check that counter is working
        assert request_counts.get("testclient", 0) > 0

    def test_security_headers_middleware(self):
        """Test security headers middleware."""
        app = FastVimes(db_path=":memory:")

        @app.middleware("http")
        async def security_headers(request: Request, call_next):
            response = await call_next(request)

            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"

            return response

        client = TestClient(app)

        response = client.get("/docs")

        # Check security headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

    def test_middleware_order(self):
        """Test middleware execution order."""
        app = FastVimes(db_path=":memory:")

        execution_order = []

        @app.middleware("http")
        async def first_middleware(request: Request, call_next):
            execution_order.append("first_start")
            response = await call_next(request)
            execution_order.append("first_end")
            return response

        @app.middleware("http")
        async def second_middleware(request: Request, call_next):
            execution_order.append("second_start")
            response = await call_next(request)
            execution_order.append("second_end")
            return response

        client = TestClient(app)

        client.get("/docs")

        # Middleware should execute in LIFO order
        assert execution_order == [
            "second_start",
            "first_start",
            "first_end",
            "second_end",
        ]

    def test_cors_middleware_setup(self):
        """Test CORS middleware can be added."""
        app = FastVimes(db_path=":memory:")

        # Add CORS middleware
        from fastapi.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        client = TestClient(app)

        # Test that CORS middleware is added without errors
        response = client.get("/docs")
        assert response.status_code == 200

    def test_authentication_middleware_concept(self):
        """Test authentication middleware concept."""
        app = FastVimes(db_path=":memory:")

        # Create test table
        app.connection.raw_sql("CREATE TABLE test_table (id INTEGER)")

        # Add auth middleware that allows all requests
        @app.middleware("http")
        async def auth_middleware(request: Request, call_next):
            # Simple auth check
            auth_header = request.headers.get("Authorization")
            if auth_header:
                request.state.authenticated = True
            else:
                request.state.authenticated = False

            response = await call_next(request)
            return response

        # Add test endpoint (using api/ prefix to avoid conflicts)
        @app.get("/api/test-auth")
        async def test_auth(request: Request):
            return {"authenticated": getattr(request.state, "authenticated", False)}

        client = TestClient(app)

        # Test without auth
        response = client.get("/api/test-auth")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False

        # Test with auth
        response = client.get(
            "/api/test-auth", headers={"Authorization": "Bearer token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
