"""Playwright configuration for FastVimes UI testing with MCP integration."""

from pathlib import Path


# Playwright configuration for MCP tools
config = {
    "browsers": ["chromium"],  # Start with Chromium only
    "headless": True,
    "viewport": {"width": 1280, "height": 720},
    "timeout": 30000,  # 30 second timeout
    "screenshot_on_failure": True,
    "video_on_failure": False,  # Disable video to save space
    "trace_on_failure": False,  # Disable trace to save space
    "base_url": "http://localhost:8000",
    "output_dir": "test-results",
}

# Test directories and patterns
test_config = {
    "testdir": "tests",
    "test_files": "test_*_playwright.py",
    "screenshot_dir": "test-results/screenshots",
    "baseline_dir": "test-results/baselines",
}

# MCP Playwright configuration
mcp_config = {
    "server_start_timeout": 30,  # seconds to wait for server startup
    "server_port": 8000,
    "server_host": "localhost",
    "test_data_db": "demo.db",  # Use demo.db for testing
}

# Ensure test directories exist


def ensure_test_dirs():
    """Create test directories if they don't exist."""
    for dir_name in ["test-results", "test-results/screenshots", "test-results/baselines"]:
        Path(dir_name).mkdir(parents=True, exist_ok=True)


# Auto-create directories when config is imported
ensure_test_dirs()
