"""Configuration management using pydantic-settings."""


from pydantic_settings import BaseSettings, SettingsConfigDict


class FastVimesSettings(BaseSettings):
    """FastVimes configuration with full-depth environment variable support."""

    model_config = SettingsConfigDict(
        env_prefix="FASTVIMES_",
        env_file=".env",
        toml_file="fastvimes.toml",
        env_nested_delimiter="__",
    )

    # Database settings
    db_path: str = ":memory:"
    sample_data_enabled: bool = True

    # Server settings
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False

    # UI settings
    title: str = "FastVimes"
    embedded_ui_enabled: bool = True

    # DuckDB UI settings
    duckdb_ui_enabled: bool = True
    duckdb_ui_port: int = 4213
    duckdb_ui_auto_launch: bool = True

    # Security settings
    read_only: bool = False
    admin_enabled: bool = True

    # Authentication settings (Authlib OAuth/OpenID Connect)
    auth_enabled: bool = False
    auth_secret_key: str | None = None

    # OAuth Configuration
    oauth_client_id: str = ""
    oauth_client_secret: str = ""
    oauth_redirect_uri: str = "http://localhost:8000/auth/callback"
    oauth_scopes: list[str] = ["openid", "email", "profile"]

    # Authorization Configuration
    require_auth_for_read: bool = False
    require_auth_for_write: bool = True
    admin_users: list[str] = []
