# Customization Guide

## Static HTML + HTMX Architecture

FastVimes uses static HTML files that load content via HTMX endpoints. No template engine needed.

### Admin Interface Structure

FastVimes includes a folder of admin HTML files (enabled by default):

```html
<!-- /admin/html (main admin interface) -->
<!DOCTYPE html>
<html>
<head>
  <title>FastVimes Admin</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
</head>
<body>
  <div class="container">
    <nav hx-get="/admin/nav" hx-trigger="load"></nav>
    <main id="content" hx-get="/admin/dashboard" hx-trigger="load"></main>
  </div>
  <div hx-get="/static/header_include.html" hx-trigger="load"></div>
</body>
</html>
```

Admin interface includes:
- `/admin/html` - Main dashboard
- `/admin/tables` - Table browser
- `/admin/schema` - Schema editor
- `/admin/config` - Configuration management

### API Endpoints Generate HTML Tables

```html
<!-- GET /users/html returns this fragment -->
<div id="users-table">
  <h1 class="title">Users</h1>
  <table class="table is-striped">
    <tr><td>John</td><td>john@example.com</td></tr>
    <tr><td>Jane</td><td>jane@example.com</td></tr>
  </table>
</div>
```

## Customizing Styles

Create `static/header_include.html` (included on every page):

```html
<!-- static/header_include.html -->
<style>
.my-table { background: #f0f0f0; }
.admin-panel { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
</style>

<script>
document.addEventListener('htmx:load', function(evt) {
  console.log('Fragment loaded:', evt.detail.elt);
});
</script>
```

## FastHTML Form Generation

FastVimes auto-generates forms from Ibis table schemas using FastHTML components:

```python
# FastVimes introspects table schema and creates dataclass + form
@app.get("/users/new")
def new_user_form():
    # Auto-generated from users table schema
    User = app.get_table_dataclass("users")
    form = app.generate_form(User, action="/users", hx_target="#result")
    return form

@app.post("/users") 
def create_user(user: User):  # Auto-validated by FastHTML
    app.db.table("users").insert(user.__dict__)
    return Div("User created successfully!", cls="notification is-success")
```

Generated form uses FastHTML components with Bulma styling:

```python
# FastVimes generates this FastHTML form:
Form(hx_post="/users", hx_target="#result")(
    Fieldset(
        Label('Name', Input(name="name", cls="input")),
        Label('Email', Input(name="email", type="email", cls="input")),
        Label('Age', Input(name="age", type="number", cls="input")),
    ),
    Button("Create", type="submit", cls="button is-primary"),
)
```

## Form Validation & Error Handling

Validation errors are embedded in HTML response with Bulma styling:

```python
@app.post("/users")
def create_user(user: User):
    try:
        # FastHTML automatically validates dataclass
        app.db.table("users").insert(user.__dict__)
        return Div("User created!", cls="notification is-success")
    except ValidationError as e:
        # Return errors in same target div
        return Div(
            Ul(*[Li(error) for error in e.errors()]),
            cls="notification is-danger"
        )
```

## Customizing Admin Interface

Admin interface is built from static HTML files that you can override:

```python
from fastvimes import FastVimes, FastVimesSettings, AdminConfig

# Disable admin entirely
app = FastVimes(config=FastVimesSettings(
    admin=AdminConfig(enabled=False)
))
```

```toml
# Or via config file
[admin]
enabled = false
```

```bash
# Or via environment variable
export FASTVIMES_ADMIN_ENABLED=false
```

Override specific admin files in your static directory:

```
static/
├── admin/
│   ├── html           # Override main dashboard  
│   ├── nav.html       # Override navigation
│   └── tables.html    # Override table browser
└── header_include.html
```

Example custom dashboard:
```html
<!-- static/admin/html -->
<div class="hero is-primary">
  <div class="hero-body">
    <h1 class="title">Custom Dashboard</h1>
  </div>
</div>
<div hx-get="/users/html" hx-trigger="load"></div>
```
