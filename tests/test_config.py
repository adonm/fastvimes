"""Test configuration management."""

import pytest
from pydantic import ValidationError

from fastvimes.config import FastVimesSettings, TableConfig


class TestTableConfig:
    """Test TableConfig model."""

    def test_defaults(self):
        """Test default values."""
        config = TableConfig()
        assert config.mode == "readonly"
        assert config.html is True
        assert config.primary_key is None
        assert config.use_rowid is True

    def test_custom_values(self):
        """Test custom values."""
        config = TableConfig(
            mode="readwrite", html=False, primary_key="user_id", use_rowid=False
        )
        assert config.mode == "readwrite"
        assert config.html is False
        assert config.primary_key == "user_id"
        assert config.use_rowid is False


class TestFastVimesSettings:
    """Test FastVimesSettings configuration."""

    def test_defaults(self):
        """Test default values."""
        settings = FastVimesSettings()
        assert settings.db_path == "data.db"
        assert settings.extensions == []
        assert settings.read_only is False
        assert settings.html_path is None
        assert settings.default_mode == "readonly"
        assert settings.default_html is True
        assert settings.tables == {}
        assert settings.admin_enabled is True

    def test_custom_values(self):
        """Test custom values."""
        settings = FastVimesSettings(
            db_path="custom.db",
            extensions=["json", "spatial"],
            read_only=False,
            html_path="/custom/html",
            default_mode="readwrite",
            default_html=False,
            tables={"users": TableConfig(mode="readwrite")},
            admin_enabled=False,
        )
        assert settings.db_path == "custom.db"
        assert settings.extensions == ["json", "spatial"]
        assert settings.read_only is False
        assert settings.html_path == "/custom/html"
        assert settings.default_mode == "readwrite"
        assert settings.default_html is False
        assert settings.tables["users"].mode == "readwrite"
        assert settings.admin_enabled is False

    def test_readonly_validation(self):
        """Test read-only validation."""
        # Valid: read-only database with readonly tables
        settings = FastVimesSettings(read_only=True, default_mode="readonly")
        assert settings.read_only is True

        # Invalid: read-only database with readwrite default
        with pytest.raises(ValueError):
            FastVimesSettings(read_only=True, default_mode="readwrite")

        # Invalid: read-only database with readwrite table
        with pytest.raises(ValueError):
            FastVimesSettings(
                read_only=True, tables={"users": TableConfig(mode="readwrite")}
            )

    def test_environment_variables(self, env_vars):
        """Test environment variable configuration."""
        env_vars(
            FASTVIMES_DB_PATH="env.db",
            FASTVIMES_READ_ONLY="true",
            FASTVIMES_DEFAULT_MODE="readonly",
            FASTVIMES_ADMIN_ENABLED="false",
        )

        settings = FastVimesSettings()
        assert settings.db_path == "env.db"
        assert settings.read_only is True
        assert settings.default_mode == "readonly"
        assert settings.admin_enabled is False

    def test_nested_environment_variables(self, env_vars):
        """Test nested environment variables."""
        env_vars(
            FASTVIMES_TABLES_USERS_MODE="readwrite",
            # Note: Complex nested env vars like primary_key are not supported
            # Use TOML config files for complex table configuration
        )

        settings = FastVimesSettings()
        # Check that nested settings are parsed correctly
        assert "users" in settings.tables
        assert settings.tables["users"].mode == "readwrite"
        # Complex nested fields should use TOML config instead of env vars

    def test_boolean_parsing(self, env_vars):
        """Test boolean environment variable parsing."""
        test_cases = [("true", True), ("false", False), ("1", True), ("0", False)]

        for env_val, expected in test_cases:
            env_vars(FASTVIMES_READ_ONLY=env_val)
            settings = FastVimesSettings()
            assert settings.read_only is expected

    def test_invalid_boolean(self, env_vars):
        """Test invalid boolean values."""
        env_vars(FASTVIMES_READ_ONLY="invalid")
        with pytest.raises(ValidationError):
            FastVimesSettings()
