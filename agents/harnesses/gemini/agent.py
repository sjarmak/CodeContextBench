"""Gemini harness agent wired to Harbor's Gemini CLI with shared guidance."""

from harbor.agents.installed.gemini_cli import GeminiCli

from ..base import BaselineHarnessMixin


class GeminiHarnessAgent(BaselineHarnessMixin, GeminiCli):
    """Gemini CLI agent extended with evaluation context and MCP wiring."""
