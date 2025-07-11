"""Test FastAPI dependencies for query parameter parsing."""

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from fastvimes.dependencies import (
    QueryParams,
    get_filters,
    get_limit,
    get_offset,
    get_pagination,
    get_sort,
    get_sorting,
)


class TestQueryParams:
    """Test QueryParams class."""

    def test_query_params_initialization(self):
        """Test QueryParams initialization."""
        # Create a mock request
        app = FastAPI()

        @app.get("/test")
        def test_endpoint(request: Request):
            query_params = QueryParams(request)
            return {"filters": query_params.filters}

        client = TestClient(app)
        response = client.get("/test?id=1&name=alice")

        assert response.status_code == 200
        data = response.json()
        assert "filters" in data

    def test_filters_parsing(self):
        """Test RQL filter parsing."""
        app = FastAPI()

        @app.get("/test")
        def test_endpoint(request: Request):
            query_params = QueryParams(request)
            return query_params.filters

        client = TestClient(app)
        response = client.get("/test?eq(id,1)&contains(name,alice)&active=true")

        assert response.status_code == 200
        data = response.json()
        
        assert "id__eq" in data["filters"]
        assert data["filters"]["id__eq"] == 1
        assert "name__contains" in data["filters"]
        assert data["filters"]["name__contains"] == "alice"
        assert "active__eq" in data["filters"]
        assert data["filters"]["active__eq"] == True

    def test_pagination_parsing(self):
        """Test pagination parameter parsing."""
        app = FastAPI()

        @app.get("/test")
        def test_endpoint(request: Request):
            query_params = QueryParams(request)
            limit, offset = query_params.get_pagination()
            return {"limit": limit, "offset": offset}

        client = TestClient(app)
        response = client.get("/test?limit=10&offset=20")

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 10
        assert data["offset"] == 20

    def test_pagination_invalid_values(self):
        """Test pagination with invalid values."""
        app = FastAPI()

        @app.get("/test")
        def test_endpoint(request: Request):
            query_params = QueryParams(request)
            limit, offset = query_params.get_pagination()
            return {"limit": limit, "offset": offset}

        client = TestClient(app)
        response = client.get("/test?limit=invalid&offset=also_invalid")

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] is None
        assert data["offset"] is None

    def test_sorting_parsing(self):
        """Test sorting parameter parsing."""
        app = FastAPI()

        @app.get("/test")
        def test_endpoint(request: Request):
            query_params = QueryParams(request)
            return {"sort": query_params.get_sorting()}

        client = TestClient(app)
        response = client.get("/test?sort=name")

        assert response.status_code == 200
        data = response.json()

        assert data["sort"] == "name"

    def test_ordering_alias(self):
        """Test ordering parameter as alias for sort."""
        app = FastAPI()

        @app.get("/test")
        def test_endpoint(request: Request):
            query_params = QueryParams(request)
            return {"ordering": query_params.get_ordering()}

        client = TestClient(app)
        response = client.get("/test?order=created_at")

        assert response.status_code == 200
        data = response.json()

        assert data["ordering"] == "created_at"


class TestDependencies:
    """Test FastAPI dependencies."""

    def test_get_filters_dependency(self):
        """Test get_filters dependency."""
        app = FastAPI()

        @app.get("/test")
        def test_endpoint(filters: dict = Depends(get_filters)):
            return filters

        client = TestClient(app)
        response = client.get("/test?eq(id,1)&contains(name,alice)")

        assert response.status_code == 200
        data = response.json()
        
        assert "id__eq" in data
        assert data["id__eq"] == 1
        assert "name__contains" in data
        assert data["name__contains"] == "alice"

    def test_get_pagination_dependency(self):
        """Test get_pagination dependency."""
        app = FastAPI()

        @app.get("/test")
        def test_endpoint(pagination: tuple = Depends(get_pagination)):
            limit, offset = pagination
            return {"limit": limit, "offset": offset}

        client = TestClient(app)
        response = client.get("/test?limit=15&offset=30")

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 15
        assert data["offset"] == 30

    def test_get_sorting_dependency(self):
        """Test get_sorting dependency."""
        app = FastAPI()

        @app.get("/test")
        def test_endpoint(sort: str = Depends(get_sorting)):
            return {"sort": sort}

        client = TestClient(app)
        response = client.get("/test?sort=updated_at")

        assert response.status_code == 200
        data = response.json()

        assert data["sort"] == "updated_at"

    def test_individual_parameter_dependencies(self):
        """Test individual parameter dependencies."""
        app = FastAPI()

        @app.get("/test")
        def test_endpoint(
            limit: int = get_limit,
            offset: int = get_offset,
            sort: str = get_sort,
        ):
            return {"limit": limit, "offset": offset, "sort": sort}

        client = TestClient(app)
        response = client.get("/test?limit=25&offset=50&sort=name")

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 25
        assert data["offset"] == 50
        assert data["sort"] == "name"

    def test_combined_dependencies(self):
        """Test combining multiple dependencies."""
        app = FastAPI()

        @app.get("/test")
        def test_endpoint(
            filters: dict = Depends(get_filters),
            pagination: tuple = Depends(get_pagination),
            sort: str = Depends(get_sorting),
        ):
            limit, offset = pagination
            return {
                "filters": filters,
                "limit": limit,
                "offset": offset,
                "sort": sort,
            }

        client = TestClient(app)
        response = client.get(
            "/test?gt(id,5)&contains(name,alice)&limit=10&offset=20&sort=created_at"
        )

        assert response.status_code == 200
        data = response.json()

        assert "id__gt" in data["filters"]
        assert data["filters"]["id__gt"] == 5
        assert "name__contains" in data["filters"]
        assert data["filters"]["name__contains"] == "alice"
        assert data["limit"] == 10
        assert data["offset"] == 20
        assert data["sort"] == "created_at"

    def test_dependencies_with_no_parameters(self):
        """Test dependencies when no query parameters are provided."""
        app = FastAPI()

        @app.get("/test")
        def test_endpoint(
            filters: dict = Depends(get_filters),
            pagination: tuple = Depends(get_pagination),
            sort: str = Depends(get_sorting),
        ):
            limit, offset = pagination
            return {
                "filters": filters,
                "limit": limit,
                "offset": offset,
                "sort": sort,
            }

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        data = response.json()

        assert data["filters"] == {}
        assert data["limit"] is None
        assert data["offset"] is None
        assert data["sort"] is None
