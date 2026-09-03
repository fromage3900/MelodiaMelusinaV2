"""Grandmaster Melodia Melusina (GMM) — unified UE 5.8 addon utility.

Combines MelodiaCore editor tools, Melusina rig management,
in-UE Surreal/Escher procedural geometry, and Monolith MCP automation
under one EnvUI umbrella.

Version: 0.2.0 (PCG governance)
"""
from __future__ import annotations

VERSION = "0.2.0"
VERSION_NAME = "Grandmaster Melodia Melusina"
VERSION_TAG = "pcg-governance"

from gmm.ui.register import register_gmm_menus, unregister_gmm_menus
