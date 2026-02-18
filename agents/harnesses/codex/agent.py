"""Codex harness agent using Harbor's Codex CLI and shared baseline guidance."""

from harbor.agents.installed.codex import Codex

from ..base import BaselineHarnessMixin


class CodexHarnessAgent(BaselineHarnessMixin, Codex):
    """Codex CLI agent extended with evaluation context and MCP wiring."""
