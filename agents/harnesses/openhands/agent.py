"""OpenHands harness agent wired to Harbor's OpenHands CLI with shared baseline tooling."""

import os

from harbor.agents import utils as harbor_utils
from harbor.agents.installed.openhands import OpenHands

from ..base import BaselineHarnessMixin

# Codex model names (LiteLLM/Harbor don't know these); we map them to OPENAI_API_KEY
# so Harbor's get_api_key_var_names_from_model_name can resolve the key.
_CODEX_MODEL_PREFIXES = ("gpt-5.3-codex", "gpt53codex", "codex")


def _get_api_key_var_names_from_model_name(model_name: str) -> list[str]:
    """Wrap Harbor's resolver so Codex models map to OPENAI_API_KEY or CODEX_API_KEY."""
    lower = (model_name or "").strip().lower()
    if lower in _CODEX_MODEL_PREFIXES or (lower and "codex" in lower and "gpt" in lower):
        if os.environ.get("CODEX_API_KEY"):
            return ["CODEX_API_KEY"]
        if os.environ.get("OPENAI_API_KEY"):
            return ["OPENAI_API_KEY"]
        # Harbor will raise "Unset API variable"; prefer telling user to set CODEX_API_KEY
        return ["CODEX_API_KEY"]
    return _original_get_api_key_var_names(model_name)


# Apply once at import so Harbor's OpenHands sees it. Harbor's openhands.py does
# "from harbor.agents.utils import get_api_key_var_names_from_model_name", so we
# must patch the openhands module's reference too (utils patch alone is not seen there).
_original_get_api_key_var_names = harbor_utils.get_api_key_var_names_from_model_name
harbor_utils.get_api_key_var_names_from_model_name = _get_api_key_var_names_from_model_name
import sys
_openhands_mod = sys.modules.get("harbor.agents.installed.openhands")
if _openhands_mod is not None:
    _openhands_mod.get_api_key_var_names_from_model_name = _get_api_key_var_names_from_model_name


def _litellm_codex_model(model_name: str) -> str:
    """Return LiteLLM model string for Codex so the container uses the OpenAI provider."""
    if not model_name or not model_name.strip():
        return model_name
    s = model_name.strip()
    lower = s.lower()
    if lower in _CODEX_MODEL_PREFIXES or ("codex" in lower and "gpt" in lower):
        return f"openai/{s}" if not s.startswith("openai/") else s
    return model_name


class OpenHandsHarnessAgent(BaselineHarnessMixin, OpenHands):
    """OpenHands CLI agent extended with evaluation context and MCP wiring."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # LiteLLM inside the container needs a provider prefix (e.g. openai/gpt-5.3-codex)
        # or it raises "LLM Provider NOT provided". Normalize Codex models so env LLM_MODEL works.
        if self.model_name:
            self.model_name = _litellm_codex_model(self.model_name)
