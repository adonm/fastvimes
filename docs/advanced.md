# Advanced Usage

## Custom Endpoints

Mix auto-generated tables with custom endpoints:

```python
from fastvimes import FastVimes, FastVimesSettings
import ibis

app = FastVimes(config=FastVimesSettings(
    db_path="analytics.db",
    default=TableConfig(mode="readwrite")
))

# Custom business logic endpoints
@app.get("/revenue")
def get_revenue(start_date: str, end_date: str):
    return app.db.table("orders").filter(
        ibis._.date.between(start_date, end_date)
    ).aggregate(
        revenue=ibis._.amount.sum()
    ).to_pandas()

@app.post("/bulk-update")
def bulk_update(table: str, updates: list):
    # Custom bulk operations
    pass

if __name__ == "__main__":
    app.run()  # Use: uv run myapp.py serve
```

## Complex Configurations

Use hierarchical configuration (see AGENT.md for complete schema):

```python
from fastvimes import FastVimes, FastVimesSettings, TableConfig

app = FastVimes(config=FastVimesSettings(
    db_path="data.db",
    extensions=["spatial", "httpfs"],
    read_only=False,
    default=TableConfig(mode="readonly", html=True),
    tables={
        "users": TableConfig(mode="readwrite", primary_key="email"),
        "orders": TableConfig(mode="readwrite"),
        "logs": TableConfig(html=False)  # API only
    }
))
```

## Schema Handling

FastVimes handles schemas using dot notation for both URLs and CLI:

```python
from fastvimes import FastVimes, FastVimesSettings, TableConfig

# Configure schema tables
app = FastVimes(config=FastVimesSettings(
    db_path="data.db",
    tables={
        "public.users": TableConfig(mode="readwrite"),
        "analytics.orders": TableConfig(mode="readonly"),
        "staging.temp_data": TableConfig(mode="readwrite")
    }
))

# Access via URLs:
# GET /public.users
# GET /analytics.orders/html
# POST /staging.temp_data
```

```bash
# CLI access with schemas
uv run fastvimes query public.users --limit 10
uv run fastvimes query analytics.orders --select date,amount --order date
uv run fastvimes create staging.temp_data --name "test" --value 123
uv run myapp.py query staging.temp_data --limit 5
```

## DuckDB Extensions for Other Databases

FastVimes uses DuckDB exclusively but supports other databases via extensions:

```python
# PostgreSQL via DuckDB extension (loaded through Ibis)
from fastvimes import FastVimes, FastVimesSettings, TableConfig

app = FastVimes(config=FastVimesSettings(
    db_path="duckdb://",
    extensions=["postgres"],
    tables={
        "pg.users": TableConfig(mode="readwrite"),
        "pg.orders": TableConfig(mode="readonly")
    }
))

# Attach external database
app.db.sql("ATTACH 'postgresql://user:pass@host/db' AS pg")
```

```python
# S3/DuckLake mode for data lakes (read-only database)
app = FastVimes(config=FastVimesSettings(
    db_path="duckdb://",
    extensions=["httpfs"],
    read_only=True,  # When database is read-only...
    tables={
        "s3_data": TableConfig(mode="readonly")  # ...all tables must be readonly
    }
))

# Query S3 data directly via external files
# Note: FastVimesSettings validates that read_only=True requires all tables to be readonly
```

## Database Views for Complex Queries

Create views in the admin interface instead of complex API parameters:

```sql
-- Create in /admin/html
CREATE VIEW user_stats AS
SELECT 
    u.name,
    u.email,
    COUNT(o.id) as order_count,
    SUM(o.amount) as total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name, u.email;
```

Now query the view:
```bash
GET /user_stats?total_spent=gt.100
```

## Custom Data Validation

Add validation using dataclasses with pydantic-settings:

```python
from dataclasses import dataclass
from fastvimes import FastVimes, FastVimesSettings, TableConfig

@dataclass
class User:
    name: str
    email: str
    age: int
    
    def __post_init__(self):
        if '@' not in self.email:
            raise ValueError('Invalid email')

app = FastVimes(config=FastVimesSettings(
    tables={
        "users": TableConfig(mode="readwrite", model=User)
    }
))
```

## Authentication Middleware

FastVimes uses standard FastAPI middleware that runs on ALL endpoints:

```python
from fastapi import Request, HTTPException

# Header-based identity middleware (runs on all endpoints)
@app.middleware("http")
async def identity_middleware(request: Request, call_next):
    user_id = request.headers.get("X-User-ID")
    role = request.headers.get("X-User-Role")
    
    # Store in request state for use in endpoints
    request.state.user_id = user_id
    request.state.role = role
    
    response = await call_next(request)
    return response

# Endpoints can access request.state for filtering
@app.get("/users")
def get_users(request: Request):
    query = app.db.table("users")
    if request.state.role != "admin":
        query = query.filter(query.user_id == request.state.user_id)
    return query.to_pandas()
```

## External Auth Integration

FastVimes integrates with any external auth system via headers:

```python
from fastapi import Request, HTTPException
import jwt
import requests

# Authelia forward auth example
@app.middleware("http")
async def authelia_middleware(request: Request, call_next):
    user = request.headers.get("Remote-User")
    groups = request.headers.get("Remote-Groups", "").split(",")
    email = request.headers.get("Remote-Email")
    name = request.headers.get("Remote-Name")
    
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    request.state.user_id = user
    request.state.email = email
    request.state.name = name
    request.state.groups = groups
    request.state.is_admin = "admin" in groups
    
    response = await call_next(request)
    return response

# Authentik forward auth example
@app.middleware("http")
async def authentik_middleware(request: Request, call_next):
    user = request.headers.get("X-authentik-username")
    groups = request.headers.get("X-authentik-groups", "").split("|")
    email = request.headers.get("X-authentik-email")
    name = request.headers.get("X-authentik-name")
    
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    request.state.user_id = user
    request.state.email = email
    request.state.name = name
    request.state.groups = groups
    request.state.is_admin = "admin" in groups
    
    response = await call_next(request)
    return response

# AWS Cognito JWT verification example
@app.middleware("http") 
async def cognito_middleware(request: Request, call_next):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token:
        try:
            # Verify Cognito JWT using PyJWT (AWS recommended approach)
            jwks = await get_cognito_jwks()  # Fetch from JWKS URI
            header = jwt.get_unverified_header(token)
            key = find_key(jwks, header["kid"])
            
            payload = jwt.decode(
                token, 
                key, 
                algorithms=["RS256"],
                audience="your-cognito-client-id",
                issuer=f"https://cognito-idp.region.amazonaws.com/user-pool-id"
            )
            
            request.state.user_id = payload["sub"]
            request.state.email = payload["email"]
            request.state.username = payload["cognito:username"]
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    response = await call_next(request)
    return response

async def get_cognito_jwks():
    """Fetch and cache Cognito JWKS"""
    # Implementation: fetch from https://cognito-idp.region.amazonaws.com/user-pool-id/.well-known/jwks.json
    pass

def find_key(jwks, kid):
    """Find the correct signing key by kid"""
    # Implementation: match kid from JWT header with JWKS keys
    pass
```

## Environment Configuration

Use pydantic-settings environment variables (see AGENT.md for complete schema):

```bash
# Production environment
export FASTVIMES_DB_PATH=/data/production.db
export FASTVIMES_EXTENSIONS=spatial,httpfs
export FASTVIMES_READ_ONLY=true
export FASTVIMES_DEFAULT_MODE=readonly
export FASTVIMES_ADMIN_ENABLED=false
export FASTVIMES_TABLES_USERS_MODE=readwrite

# Development environment  
export FASTVIMES_DB_PATH=./dev.db
export FASTVIMES_DEFAULT_MODE=readwrite
export FASTVIMES_ADMIN_ENABLED=true
```

## CLI Command Structure

FastVimes CLI actions mirror the API endpoints exactly:

```bash
# CLI Action -> API Endpoint
uv run fastvimes query users --limit 10 -> GET /users?limit=10
uv run fastvimes create users --name "John" -> POST /users {"name": "John"}
uv run fastvimes update users --id 1 --name "Jane" -> PUT /users?id=1 {"name": "Jane"}
uv run fastvimes delete users --id 1 -> DELETE /users?id=1

# All CLI actions use the same code paths as API endpoints
```

## Testing

```python
# tests/test_app.py
def test_auto_generated_api():
    response = client.get("/users")
    assert response.status_code == 200
    assert "users" in response.json()
```
