"""Core framework — MCP client, audit, registry, settings."""
from __future__ import annotations

from gmm.core.mcp_client import MonolithClient
from gmm.core.audit import write_audit, audit_dir, GmmAudit
from gmm.core.settings import GmmSettings
