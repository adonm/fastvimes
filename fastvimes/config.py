import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TableConfig(BaseModel):
    mode: str = Field("readonly", pattern="^(readonly|readwrite)$")
    html: bool = True
    primary_key: str | None = None
    use_rowid: bool = True


class FastVimesSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FASTVIMES_", env_nested_delimiter="_", toml_file="fastvimes.toml"
    )

    # Database settings
    db_path: str = "data.db"
    extensions: list[str] = []
    read_only: bool = False

    # Interface settings
    html_path: str | None = None
    admin_enabled: bool = True

    # Default table settings
    default_mode: str = Field("readonly", pattern="^(readonly|readwrite)$")
    default_html: bool = True
    default_primary_key: str | None = None
    default_use_rowid: bool = True

    # Per-table overrides (loaded from [tables.NAME] sections)
    tables: dict[str, TableConfig] = {}

    @field_validator("extensions")
    @classmethod
    def validate_extensions(cls, v: list[str]) -> list[str]:
        """Validate extension names."""
        for ext in v:
            if not ext or " " in ext:
                raise ValueError(f"Invalid extension name: {ext}")
        return v

    @classmethod
    def from_toml(cls, config_path: str | Path) -> "FastVimesSettings":
        """Load settings from a TOML file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "rb") as f:
            config_data = tomllib.load(f)

        return cls(**config_data)

    def get_table_config(self, table_name: str) -> TableConfig:
        """Get configuration for a specific table, using defaults if not specified."""
        if table_name in self.tables:
            return self.tables[table_name]

        # Return default configuration
        return TableConfig(
            mode=self.default_mode,
            html=self.default_html,
            primary_key=self.default_primary_key,
            use_rowid=self.default_use_rowid,
        )

    def model_post_init(self, __context: Any) -> None:
        """Validate configuration consistency."""
        if self.read_only:
            # If database is read-only, all tables must be readonly
            if self.default_mode == "readwrite":
                raise ValueError(
                    "Cannot use readwrite mode when database is read_only=True"
                )
            for table_name, config in self.tables.items():
                if config.mode == "readwrite":
                    raise ValueError(
                        f"Table '{table_name}' cannot use readwrite mode when database is read_only=True"
                    )
