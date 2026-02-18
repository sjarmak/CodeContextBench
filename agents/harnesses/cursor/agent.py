"""Cursor harness agent wired to Harbor's Cursor CLI with shared guidance."""

from harbor.agents.installed.cursor_cli import CursorCli

from ..base import BaselineHarnessMixin


class CursorHarnessAgent(BaselineHarnessMixin, CursorCli):
    """Cursor CLI agent extended with evaluation context and MCP wiring."""
