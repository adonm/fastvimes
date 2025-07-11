# Customization Guide

## HTMX Fragment Architecture

FastVimes follows HTMX best practices with a clear separation between full pages and fragments:

### **Main Pages** (Full HTML Documents)
Load all dependencies and provide the application shell:
- **Bulma CSS**: `https://unpkg.com/bulma@1.0.4/css/bulma.css`
- **HTMX**: `https://unpkg.com/htmx.org@2.0.6/dist/htmx.js`
- **Font Awesome**: `https://use.fontawesome.com/releases/v5.15.4/js/all.js`

### **Fragments** (Partial HTML)
Return only the content that gets swapped into the main page:
- No `<html>`, `<head>`, or `<body>` tags
- No CSS/JS dependencies (already loaded in main page)
- Pure content with Bulma classes for styling

### **URL Pattern**
- **Main pages**: `/admin`, `/dashboard` (full HTML)
- **Fragments**: `/{table}/html`, `/admin/nav` (partial HTML)

### Example: Main Admin Page

```html
<!-- /admin (full HTML document) -->
<!DOCTYPE html>
<html>
<head>
  <title>FastVimes Admin</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://unpkg.com/bulma@1.0.4/css/bulma.css">
  <script src="https://unpkg.com/htmx.org@2.0.6/dist/htmx.js"></script>
</head>
<body>
  <div class="container">
    <!-- Navigation loads as fragment -->
    <nav hx-get="/admin/nav" hx-trigger="load"></nav>
    
    <!-- Main content area for swapping -->
    <main id="content" hx-get="/admin/tables" hx-trigger="load"></main>
  </div>
  
  <!-- Custom styles loaded as fragment -->
  <div hx-get="/static/header_include.html" hx-trigger="load"></div>
</body>
</html>
```

### Example: Fragment Response

```html
<!-- GET /{table}/html returns this fragment (no <html>, <head>, etc.) -->
<div id="users-table">
  <h1 class="title">Users</h1>
  <div class="buttons mb-4">
    <button class="button is-primary" hx-get="/users/html/new" hx-target="#content">
      <span class="icon"><i class="fas fa-plus"></i></span>
      <span>Add User</span>
    </button>
  </div>
  
  <table class="table is-fullwidth is-striped">
    <thead>
      <tr><th>Name</th><th>Email</th><th>Actions</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>John</td>
        <td>john@example.com</td>
        <td>
          <button class="button is-small is-info" 
                  hx-get="/users/1/html/edit" 
                  hx-target="#content">Edit</button>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

### Navigation Fragment

```html
<!-- GET /admin/nav returns this fragment -->
<nav class="navbar" role="navigation">
  <div class="navbar-brand">
    <span class="navbar-item"><strong>FastVimes Admin</strong></span>
  </div>
  <div class="navbar-menu">
    <div class="navbar-start">
      <a class="navbar-item" hx-get="/admin/tables" hx-target="#content">Tables</a>
      <a class="navbar-item" hx-get="/admin/schema" hx-target="#content">Schema</a>
      <a class="navbar-item" hx-get="/admin/config" hx-target="#content">Config</a>
    </div>
  </div>
</nav>
```

## Customizing Styles

Create `static/header_include.html` (included on every page):

```html
<!-- static/header_include.html -->
<style>
/* Custom styles (Bulma CSS already loaded via CDN) */
.my-table { background: #f0f0f0; }
.fastvimes-gradient { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.custom-card { border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
</style>

<script>
/* Custom JavaScript (HTMX already loaded via CDN) */
document.addEventListener('htmx:load', function(evt) {
  console.log('Fragment loaded:', evt.detail.elt);
});

document.addEventListener('DOMContentLoaded', function() {
  console.log('FastVimes application loaded');
});
</script>
```

## Form Generation (Fragments)

FastVimes auto-generates form fragments from table schemas:

```python
# Form endpoints return fragments (no full HTML page)
@app.get("/users/html/new")
def new_user_form():
    """Return form fragment for HTMX swapping."""
    User = app.get_table_dataclass("users")
    
    # Generate form fragment (no <html>, <head>, etc.)
    form_html = app.form_generator.generate_form(
        User, 
        action="/users", 
        method="POST"
    )
    
    # Return fragment with HTMX attributes
    return f'''
    <div class="box">
        <h2 class="title is-4">New User</h2>
        {form_html}
        <div class="buttons mt-4">
            <button class="button" hx-get="/users/html" hx-target="#content">
                Cancel
            </button>
        </div>
    </div>
    '''

@app.post("/users") 
def create_user(user: User):
    """Create user and return success fragment."""
    app.db.table("users").insert(user.__dict__)
    
    # Return success message fragment
    return '''
    <div class="notification is-success">
        <strong>Success!</strong> User created successfully.
        <button class="button is-small is-success" 
                hx-get="/users/html" 
                hx-target="#content">
            View Users
        </button>
    </div>
    '''
```

### Form Fragment Structure

```html
<!-- Form fragments include HTMX attributes and Bulma styling -->
<form hx-post="/users" hx-target="#content" class="box">
  <div class="field">
    <label class="label">Name</label>
    <div class="control">
      <input class="input" type="text" name="name" required>
    </div>
  </div>
  
  <div class="field">
    <label class="label">Email</label>
    <div class="control">
      <input class="input" type="email" name="email" required>
    </div>
  </div>
  
  <div class="field">
    <div class="control">
      <button type="submit" class="button is-primary">
        <span class="icon"><i class="fas fa-save"></i></span>
        <span>Save User</span>
      </button>
    </div>
  </div>
</form>
```

## Error Handling (Fragments)

Validation errors return fragments with Bulma styling:

```python
@app.post("/users")
def create_user(user: User):
    try:
        app.db.table("users").insert(user.__dict__)
        # Return success fragment
        return '''
        <div class="notification is-success">
            <button class="delete"></button>
            <strong>Success!</strong> User created successfully.
        </div>
        '''
    except ValidationError as e:
        # Return error fragment (not full page)
        errors_html = ''.join(f'<li>{error}</li>' for error in e.errors())
        return f'''
        <div class="notification is-danger">
            <button class="delete"></button>
            <strong>Validation Error</strong>
            <ul>{errors_html}</ul>
        </div>
        '''
    except Exception as e:
        # Return error fragment
        return f'''
        <div class="notification is-danger">
            <button class="delete"></button>
            <strong>Error:</strong> {str(e)}
        </div>
        '''
```

## Customizing Admin Interface

Admin interface is built from static HTML files that you can override:

```python
from fastvimes import FastVimes, FastVimesSettings

# Disable admin entirely
app = FastVimes(config=FastVimesSettings(
    admin_enabled=False
))
```

```toml
# Or via config file
admin_enabled = false
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
