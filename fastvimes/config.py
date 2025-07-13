"""Configuration management using pydantic-settings."""

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class FastVimesSettings(BaseSettings):
    """FastVimes configuration with full-depth environment variable support."""
    
    model_config = SettingsConfigDict(
        env_prefix='FASTVIMES_',
        env_file='.env',
        toml_file='fastvimes.toml',
        env_nested_delimiter='__'
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
    
    # Security settings
    read_only: bool = False
    admin_enabled: bool = True
