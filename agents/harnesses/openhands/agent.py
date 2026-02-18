"""OpenHands harness agent wired to Harbor's OpenHands CLI with shared baseline tooling."""

from harbor.agents.installed.openhands import OpenHands

from ..base import BaselineHarnessMixin


class OpenHandsHarnessAgent(BaselineHarnessMixin, OpenHands):
    """OpenHands CLI agent extended with evaluation context and MCP wiring."""
