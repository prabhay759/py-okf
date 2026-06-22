"""Shared fixtures for py-okf tests."""

import pytest
from pathlib import Path

SAMPLE_MODULE_SRC = '''\
"""A sample module for testing py-okf."""

from typing import Optional, List

__all__ = ["query"]

TIMEOUT: int = 30

class Connection:
    """Manages database connections."""

    host: str
    port: int = 5432

    def __init__(self, host: str, port: int = 5432) -> None:
        """Initialize a connection."""
        self.host = host
        self.port = port

    def connect(self) -> bool:
        """Establish the connection."""
        return True

    @classmethod
    def from_url(cls, url: str) -> "Connection":
        """Create from a URL string."""
        return cls(url)

    def _internal(self) -> None:
        pass

def query(sql: str, params: Optional[List[str]] = None) -> list:
    """Execute a SQL query."""
    return []

def _helper(x: int) -> int:
    return x
'''


@pytest.fixture
def sample_py_file(tmp_path: Path) -> Path:
    f = tmp_path / "sample.py"
    f.write_text(SAMPLE_MODULE_SRC, encoding="utf-8")
    return f


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    pkg = tmp_path / "mypackage"
    pkg.mkdir()
    (pkg / "__init__.py").write_text('"""My package."""\n', encoding="utf-8")
    (pkg / "utils.py").write_text(SAMPLE_MODULE_SRC, encoding="utf-8")
    return tmp_path


@pytest.fixture
def okf_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".okf"
    d.mkdir()
    return d
