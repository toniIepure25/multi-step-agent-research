"""
Shared pytest fixtures for the ASAR test suite.

Fixes Windows PermissionError on the default tmp_path base directory
by overriding the basetemp to a user-writable location.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def tmp_path_factory(request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory) -> pytest.TempPathFactory:
    """Return the built-in factory; the basetemp override below handles permissions."""
    return tmp_path_factory


def pytest_configure(config: pytest.Config) -> None:
    """Set a writable basetemp on Windows to avoid PermissionError."""
    if os.name == "nt" and config.option.basetemp is None:
        fallback = Path(tempfile.gettempdir()) / "asar-pytest"
        fallback.mkdir(parents=True, exist_ok=True)
        config.option.basetemp = str(fallback)
