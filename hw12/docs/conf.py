"""Sphinx configuration; imports use isolated documentation-only settings."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "documentation-only-secret-not-for-deployment")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
project = "Contacts API"
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon"]
html_theme = "alabaster"
autodoc_member_order = "bysource"
