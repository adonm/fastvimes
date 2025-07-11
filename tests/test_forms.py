"""Test forms generation functionality."""


class TestFormsGeneration:
    """Test automatic form generation from database schemas."""

    def test_form_generator_initialization(self, app_with_sample_data):
        """Test form generator initialization."""
        app = app_with_sample_data
        assert hasattr(app, "form_generator")
        assert app.form_generator is not None

    def test_form_generator_interface(self, app_with_sample_data):
        """Test form generator has expected interface."""
        app = app_with_sample_data

        # Test that form generator has generate_form method
        assert hasattr(app.form_generator, "generate_form")

        # Test that it requires model and action parameters
        UserModel = app.get_table_dataclass("users")

        # Should work with proper parameters
        form = app.form_generator.generate_form(model=UserModel, action="/users")
        assert form is not None

    def test_form_generation_with_model(self, app_with_sample_data):
        """Test form generation with Pydantic model."""
        app = app_with_sample_data

        UserModel = app.get_table_dataclass("users")

        # Generate form with model
        form = app.form_generator.generate_form(
            model=UserModel, action="/users", method="POST"
        )

        # Should return a string (HTML)
        assert isinstance(form, str)
        assert len(form) > 0

    def test_form_generation_with_data(self, app_with_sample_data):
        """Test form generation with default data."""
        app = app_with_sample_data

        UserModel = app.get_table_dataclass("users")

        # Generate form with default data
        form = app.form_generator.generate_form(
            model=UserModel,
            action="/users",
            data={"name": "Default Name", "active": True},
        )

        assert isinstance(form, str)
        assert "Default Name" in form or "value=" in form

    def test_form_generation_methods(self, app_with_sample_data):
        """Test form generation with different methods."""
        app = app_with_sample_data

        UserModel = app.get_table_dataclass("users")

        # Test POST method
        form_post = app.form_generator.generate_form(
            model=UserModel, action="/users", method="POST"
        )

        # Test PUT method
        form_put = app.form_generator.generate_form(
            model=UserModel, action="/users?eq(id,1)", method="PUT"
        )

        assert isinstance(form_post, str)
        assert isinstance(form_put, str)
        assert form_post != form_put  # Should be different

    def test_table_list_generation(self, app_with_sample_data):
        """Test table list generation."""
        app = app_with_sample_data

        # Test table list generation
        data = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
        ]

        table_html = app.form_generator.generate_table_list(
            data=data, table_name="users"
        )

        assert isinstance(table_html, str)
        assert "Alice" in table_html
        assert "Bob" in table_html

    def test_html_wrapping(self, app_with_sample_data):
        """Test HTML document wrapping."""
        app = app_with_sample_data

        content = "<p>Test content</p>"
        wrapped = app.form_generator.wrap_in_html(content, title="Test Page")

        assert isinstance(wrapped, str)
        assert "html" in wrapped.lower()  # HTML element should be present
        assert "Test Page" in wrapped  # Title should be present
        assert "Test content" in wrapped

    def test_field_type_detection(self, app_with_sample_data):
        """Test field type detection for form inputs."""
        app = app_with_sample_data

        generator = app.form_generator

        # Test type detection
        assert generator._get_input_type(int) == "number"
        assert generator._get_input_type(str) == "text"
        assert generator._get_input_type(bool) == "checkbox"
        assert generator._get_input_type(float) == "number"

    def test_field_name_formatting(self, app_with_sample_data):
        """Test field name formatting for display."""
        app = app_with_sample_data

        generator = app.form_generator

        # Test name formatting
        assert generator._format_field_name("first_name") == "First Name"
        assert generator._format_field_name("email_address") == "Email Address"
        assert generator._format_field_name("id") == "Id"

    def test_form_with_complex_model(self, app_with_sample_data):
        """Test form generation with complex model."""
        app = app_with_sample_data

        PostModel = app.get_table_dataclass("posts")

        # Generate form for posts table
        form = app.form_generator.generate_form(model=PostModel, action="/posts")

        assert isinstance(form, str)
        assert len(form) > 0

    def test_convenience_function(self, app_with_sample_data):
        """Test convenience form generation function."""
        app = app_with_sample_data

        # Import and test the convenience function
        from fastvimes.forms import generate_form_for_table

        form = generate_form_for_table(app=app, table_name="users", action="/users")

        assert isinstance(form, str)
        assert len(form) > 0
