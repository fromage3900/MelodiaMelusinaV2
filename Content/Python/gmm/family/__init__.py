"""Shared Melodia Studio/GMM project contracts."""

from .contracts import FORMAT, ROLES, STYLES
from .manifest import validate_manifest

__all__ = ["FORMAT", "ROLES", "STYLES", "validate_manifest"]
